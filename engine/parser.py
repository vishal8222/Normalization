import csv
import openpyxl
import pdfplumber
from typing import List, Dict, Tuple

def parse_csv(file_path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames if reader.fieldnames else []
        rows = []
        for row in reader:
            if any(str(v).strip() for v in row.values()):
                rows.append({k: str(v).strip() if v else "" for k, v in row.items()})
    return columns, rows

def parse_excel(file_path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active
    
    headers = [cell.value for cell in sheet[1]]
    columns = [str(h).strip() for h in headers if h is not None]
    
    rows = []
    for row in sheet.iter_rows(min_row=2):
        row_dict = {}
        is_empty = True
        for col_idx, cell in enumerate(row):
            if col_idx < len(columns):
                val = str(cell.value).strip() if cell.value is not None else ""
                row_dict[columns[col_idx]] = val
                if val:
                    is_empty = False
        if not is_empty:
            rows.append(row_dict)
            
    return columns, rows

def parse_pdf(file_path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    columns = []
    rows = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                if not columns:
                    columns = [str(h).strip().replace('\n', ' ') for h in table[0] if h]
                
                for row in table[1:]:
                    row_dict = {}
                    is_empty = True
                    for col_idx, cell in enumerate(row):
                        if col_idx < len(columns):
                            val = str(cell).strip().replace('\n', ' ') if cell else ""
                            row_dict[columns[col_idx]] = val
                            if val:
                                is_empty = False
                    if not is_empty:
                        rows.append(row_dict)
    return columns, rows
