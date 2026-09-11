from typing import List, Dict, Tuple
from models.schemas import FunctionalDependency, NormalizationViolation

class FunctionalDependencyAnalyzer:
    def __init__(self, columns: List[str], primary_key: List[str], dependencies: List[FunctionalDependency]):
        self.columns = columns
        self.primary_key = primary_key
        self.dependencies = dependencies

    def detect_1nf_violations(self, data: List[Dict]) -> List[NormalizationViolation]:
        violations = []
        multivalued_cols = set()
        
        for row in data:
            for col, val in row.items():
                if isinstance(val, str) and (',' in val or ';' in val):
                    multivalued_cols.add(col)
                    
        if multivalued_cols:
            violations.append(
                NormalizationViolation(
                    normal_form="1NF",
                    violation_type="Multivalued Attributes",
                    description=f"Columns {', '.join(multivalued_cols)} contain multiple values separated by commas or semicolons.",
                    affected_columns=list(multivalued_cols)
                )
            )
        return violations

    def auto_detect_multivalued(self, data: List[Dict]) -> List[str]:
        multivalued_cols = set()
        for row in data:
            for col, val in row.items():
                if isinstance(val, str) and (',' in val or ';' in val):
                    multivalued_cols.add(col)
        return list(multivalued_cols)

    @staticmethod
    def auto_detect_dependencies(columns: List[str], data: List[Dict]) -> List[FunctionalDependency]:
        """Automatically find functional dependencies (X -> [Y1, Y2, ...]) from data."""
        if not data or not columns:
            return []
            
        # Exclude surrogate IDs or single-row unique IDs from being trivial determinants if needed,
        # but standard pairwise FD check:
        pairwise = {}
        for x in columns:
            dependents = []
            for y in columns:
                if x == y:
                    continue
                mapping = {}
                valid = True
                for row in data:
                    val_x = row.get(x)
                    val_y = row.get(y)
                    # Ignore empty/nulls in determining if row is incomplete
                    if val_x is None:
                        continue
                    if val_x in mapping:
                        if mapping[val_x] != val_y:
                            valid = False
                            break
                    else:
                        mapping[val_x] = val_y
                if valid and mapping:
                    dependents.append(y)
            if dependents:
                pairwise[x] = dependents

        # Format into List[FunctionalDependency]
        # Clean redundant transitive groups where possible or provide clean list
        result = []
        for det, deps in pairwise.items():
            result.append(FunctionalDependency(determinant=[det], dependent=deps))
        return result

    def get_partial_dependencies(self) -> List[Tuple[List[str], List[str]]]:
        if len(self.primary_key) <= 1:
            return [] # No partial dependency possible with single-column PK
            
        pk_set = set(self.primary_key)
        partials = []
        
        for dep in self.dependencies:
            det_set = set(dep.determinant)
            # If determinant is a strict subset of primary key
            if det_set.issubset(pk_set) and len(det_set) < len(pk_set):
                partials.append((dep.determinant, dep.dependent))
                
        return partials

    def get_transitive_dependencies(self) -> List[Tuple[List[str], List[str]]]:
        pk_set = set(self.primary_key)
        transitivities = []
        
        for dep in self.dependencies:
            det_set = set(dep.determinant)
            # If determinant is not the primary key, and not a subset of it (meaning it's a non-prime attribute determining another non-prime)
            if not pk_set.issubset(det_set) and not det_set.issubset(pk_set):
                transitivities.append((dep.determinant, dep.dependent))
                
        return transitivities
