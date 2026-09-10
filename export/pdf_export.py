from fpdf import FPDF
from models.schemas import NormalizationResult
import datetime

class PdfExporter:
    def __init__(self, result: NormalizationResult):
        self.result = result
        
    def export(self, file_path: str) -> str:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Helper to add section title
        def add_title(title):
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(27, 79, 114) # dark blue
            pdf.cell(0, 10, title, ln=True, align='C')
            pdf.ln(5)
            pdf.set_text_color(0, 0, 0)
            
        # 1. Title Page
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 60, "", ln=True)
        pdf.cell(0, 10, "Database Normalization Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.cell(0, 10, f"Session ID: {self.result.session_id}", ln=True, align='C')
        
        # 2. Original Data (schema)
        pdf.add_page()
        add_title("Original Data Schema")
        pdf.set_font("Arial", '', 12)
        cols = [c.name for c in self.result.original_table.columns]
        pdf.multi_cell(0, 10, f"Columns: {', '.join(cols)}")
        
        # 3, 4, 5. Steps Analysis
        for step in self.result.steps:
            pdf.add_page()
            add_title(f"{step.normal_form} Analysis")
            
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, "Violations Found:", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            
            if not step.violations_found:
                pdf.cell(0, 10, "None", ln=True)
            else:
                for v in step.violations_found:
                    pdf.multi_cell(0, 10, f"- {v.violation_type}: {v.description} (Cols: {', '.join(v.affected_columns)})")
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Explanation:", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 10, step.explanation)
            
        # 6. Final Tables
        pdf.add_page()
        add_title("Final Normalized Tables")
        pdf.set_font("Arial", '', 10)
        for table in self.result.final_tables:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"Table: {table.name}", ln=True)
            pdf.set_font("Arial", '', 10)
            
            for col in table.columns:
                props = []
                if col.is_primary_key: props.append("PK")
                if col.is_foreign_key: props.append(f"FK -> {col.references}")
                prop_str = f" [{', '.join(props)}]" if props else ""
                pdf.cell(0, 8, f"- {col.name} ({col.data_type}){prop_str}", ln=True)
            pdf.ln(5)
            
        # 7. SQL Queries
        pdf.add_page()
        add_title("Generated SQL (DDL)")
        pdf.set_font("Courier", '', 9)
        pdf.multi_cell(0, 5, self.result.generated_ddl)
        
        pdf.output(file_path)
        return file_path
