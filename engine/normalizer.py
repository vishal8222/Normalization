from typing import List, Dict, Any, Tuple
from db.sqlite_engine import SQLiteEngine
from engine.sql_logger import SQLLogger
from engine.dependency import FunctionalDependencyAnalyzer
from engine.sql_generator import generate_mysql_ddl
from models.schemas import (
    ColumnInfo, TableInfo, FunctionalDependency, 
    NormalizationViolation, NormalizationStepResult, NormalizationResult
)

class DatabaseNormalizer:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db = SQLiteEngine()
        self.conn = self.db.create_session_db(session_id)
        self.sql_logger = SQLLogger()

    def _table_info_from_sqlite(self, table_name: str) -> TableInfo:
        cols_info = self.db.get_table_info(self.conn, table_name)
        data = self.db.get_table_data(self.conn, table_name)
        columns = [ColumnInfo(name=c['name'], data_type=c['type']) for c in cols_info]
        return TableInfo(name=table_name, columns=columns, data=data)

    def normalize(self, columns: List[str], rows: List[Dict[str, Any]], primary_key: List[str], dependencies: List[FunctionalDependency]) -> NormalizationResult:
        # Load initial data
        original_table_name = "OriginalData"
        self.db.load_data(self.conn, original_table_name, columns, rows)
        original_table = self._table_info_from_sqlite(original_table_name)
        
        analyzer = FunctionalDependencyAnalyzer(columns, primary_key, dependencies)
        
        # Steps
        steps = []
        all_sql_queries = []
        
        # 1NF
        step_1nf = self._apply_1nf(original_table_name, analyzer, rows)
        steps.append(step_1nf)
        all_sql_queries.extend(step_1nf.sql_queries)
        
        # 2NF
        step_2nf = self._apply_2nf(step_1nf.resulting_tables, primary_key, analyzer)
        steps.append(step_2nf)
        all_sql_queries.extend(step_2nf.sql_queries)
        
        # 3NF
        step_3nf = self._apply_3nf(step_2nf.resulting_tables, analyzer)
        steps.append(step_3nf)
        all_sql_queries.extend(step_3nf.sql_queries)
        
        final_tables = step_3nf.resulting_tables
        
        ddl = generate_mysql_ddl(final_tables)
        er_data = self._generate_er_data(final_tables)
        
        return NormalizationResult(
            session_id=self.session_id,
            original_table=original_table,
            steps=steps,
            final_tables=final_tables,
            generated_ddl=ddl,
            all_sql_queries=all_sql_queries,
            er_diagram_data=er_data
        )

    def _apply_1nf(self, table_name: str, analyzer: FunctionalDependencyAnalyzer, raw_data: List[Dict]) -> NormalizationStepResult:
        violations = analyzer.detect_1nf_violations(raw_data)
        multivalued_cols = analyzer.auto_detect_multivalued(raw_data)
        
        queries = []
        if multivalued_cols:
            # Simplistic 1NF fix for demonstration: we'll just log an explanation and split in Python, then recreate table
            # since sqlite doesn't have an easy string_split function natively built-in without extensions.
            
            explanation = f"Detected multi-valued attributes in columns: {', '.join(multivalued_cols)}. Normalized by creating separate rows for each value."
            
            # Read existing
            data = self.db.get_table_data(self.conn, table_name)
            new_data = []
            for row in data:
                # very simplified cartesian product split
                base_row = {k: v for k, v in row.items() if k not in multivalued_cols}
                # For simplicity, assuming one multivalued column causes multiple rows, and we split by comma
                # This is a naive implementation for the sake of the engine.
                
                # We will handle multiple multivalued columns by taking max splits (just for mock)
                splits = {c: [x.strip() for x in str(row[c]).split(',')] for c in multivalued_cols}
                max_len = max([len(v) for v in splits.values()]) if splits else 1
                
                for i in range(max_len):
                    new_row = base_row.copy()
                    for c in multivalued_cols:
                        new_row[c] = splits[c][i] if i < len(splits[c]) else splits[c][-1]
                    new_data.append(new_row)
            
            # Recreate table in 1NF
            new_table_name = table_name + "_1NF"
            cols = list(data[0].keys()) if data else []
            drop_sql = f'DROP TABLE IF EXISTS "{new_table_name}";'
            self.db.execute_and_log(self.conn, drop_sql)
            queries.append(drop_sql)
            
            self.db.load_data(self.conn, new_table_name, cols, new_data)
            queries.append(f"-- Loaded normalized 1NF data into {new_table_name}")
            
            resulting_tables = [self._table_info_from_sqlite(new_table_name)]
        else:
            explanation = "Table is already in 1NF."
            resulting_tables = [self._table_info_from_sqlite(table_name)]
            
        return NormalizationStepResult(
            normal_form="1NF",
            violations_found=violations,
            resulting_tables=resulting_tables,
            explanation=explanation,
            sql_queries=queries
        )

    def _apply_2nf(self, tables: List[TableInfo], primary_key: List[str], analyzer: FunctionalDependencyAnalyzer) -> NormalizationStepResult:
        partials = analyzer.get_partial_dependencies()
        queries = []
        resulting_tables = []
        violations = []
        
        current_table = tables[0].name
        
        if partials:
            explanation = "Detected partial dependencies. Decomposing tables to satisfy 2NF."
            
            remaining_cols = set(c.name for c in tables[0].columns)
            
            for idx, (det, dep) in enumerate(partials):
                violations.append(
                    NormalizationViolation(
                        normal_form="2NF",
                        violation_type="Partial Dependency",
                        description=f"{', '.join(dep)} depends only on {', '.join(det)} (part of PK).",
                        affected_columns=dep
                    )
                )
                
                new_table_name = f"Table_2NF_{idx+1}"
                cols_to_select = ", ".join([f'"{c}"' for c in det + dep])
                
                # Create decomposed table
                create_sql = f'CREATE TABLE "{new_table_name}" AS SELECT DISTINCT {cols_to_select} FROM "{current_table}";'
                self.db.execute_and_log(self.conn, create_sql)
                queries.append(create_sql)
                
                resulting_tables.append(self._table_info_from_sqlite(new_table_name))
                
                # Remove dependents from remaining columns
                for d in dep:
                    if d in remaining_cols:
                        remaining_cols.remove(d)
                        
            # Base table
            base_table_name = "Table_2NF_Base"
            cols_to_select = ", ".join([f'"{c}"' for c in remaining_cols])
            create_sql = f'CREATE TABLE "{base_table_name}" AS SELECT DISTINCT {cols_to_select} FROM "{current_table}";'
            self.db.execute_and_log(self.conn, create_sql)
            queries.append(create_sql)
            resulting_tables.append(self._table_info_from_sqlite(base_table_name))
            
        else:
            explanation = "No partial dependencies found. Table is in 2NF."
            resulting_tables = tables
            
        return NormalizationStepResult(
            normal_form="2NF",
            violations_found=violations,
            resulting_tables=resulting_tables,
            explanation=explanation,
            sql_queries=queries
        )

    def _apply_3nf(self, tables: List[TableInfo], analyzer: FunctionalDependencyAnalyzer) -> NormalizationStepResult:
        transitivities = analyzer.get_transitive_dependencies()
        queries = []
        final_tables = []
        violations = []
        
        if not transitivities:
            return NormalizationStepResult(
                normal_form="3NF",
                violations_found=[],
                resulting_tables=tables,
                explanation="No transitive dependencies found. Tables are in 3NF.",
                sql_queries=[]
            )
            
        explanation = "Detected transitive dependencies. Decomposing to satisfy 3NF."
        
        for table in tables:
            current_table_name = table.name
            remaining_cols = set(c.name for c in table.columns)
            
            table_transitivities = []
            for det, dep in transitivities:
                # Check if this transitivity applies to current table
                if all(d in remaining_cols for d in det) and all(d in remaining_cols for d in dep):
                    table_transitivities.append((det, dep))
                    
            if not table_transitivities:
                final_tables.append(table)
                continue
                
            for idx, (det, dep) in enumerate(table_transitivities):
                violations.append(
                    NormalizationViolation(
                        normal_form="3NF",
                        violation_type="Transitive Dependency",
                        description=f"{', '.join(dep)} depends on non-key {', '.join(det)}.",
                        affected_columns=dep
                    )
                )
                
                new_table_name = f"{current_table_name}_3NF_{idx+1}"
                cols_to_select = ", ".join([f'"{c}"' for c in det + dep])
                
                create_sql = f'CREATE TABLE "{new_table_name}" AS SELECT DISTINCT {cols_to_select} FROM "{current_table_name}";'
                self.db.execute_and_log(self.conn, create_sql)
                queries.append(create_sql)
                
                final_tables.append(self._table_info_from_sqlite(new_table_name))
                
                for d in dep:
                    if d in remaining_cols:
                        remaining_cols.remove(d)
                        
            # Base table
            base_table_name = f"{current_table_name}_3NF_Base"
            cols_to_select = ", ".join([f'"{c}"' for c in remaining_cols])
            create_sql = f'CREATE TABLE "{base_table_name}" AS SELECT DISTINCT {cols_to_select} FROM "{current_table_name}";'
            self.db.execute_and_log(self.conn, create_sql)
            queries.append(create_sql)
            final_tables.append(self._table_info_from_sqlite(base_table_name))
            
        return NormalizationStepResult(
            normal_form="3NF",
            violations_found=violations,
            resulting_tables=final_tables,
            explanation=explanation,
            sql_queries=queries
        )

    def _generate_er_data(self, tables: List[TableInfo]) -> Dict:
        nodes = []
        edges = []
        
        for table in tables:
            nodes.append({
                "id": table.name,
                "label": table.name,
                "columns": [c.name for c in table.columns]
            })
            
            # Very simplistic edge generation based on column name matching (mocking FKs)
            # In a real app, you'd use exact foreign key metadata
            for col in table.columns:
                if col.references:
                    ref_table, _ = col.references.split('(')
                    edges.append({
                        "source": table.name,
                        "target": ref_table,
                        "label": col.name
                    })
                    
        return {"nodes": nodes, "edges": edges}
