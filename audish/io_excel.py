"""
Excel I/O utilities using openpyxl.
Preserves original columns and appends scheduling fields.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def read_excel_sheet(filepath: str, sheet_name: Optional[str] = None) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Read an Excel sheet into a list of dictionaries.
    
    Args:
        filepath: Path to Excel file
        sheet_name: Name of sheet to read (None = first sheet)
        
    Returns:
        Tuple of (column_names, rows) where rows is list of dicts
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    if sheet_name:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"Sheet '{sheet_name}' not found in {filepath}. Available: {wb.sheetnames}")
        ws = wb[sheet_name]
    else:
        ws = wb.active
    
    # Read header row
    headers = []
    for cell in ws[1]:
        headers.append(cell.value if cell.value is not None else "")
    
    # Read data rows
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = {}
        for col_idx, value in enumerate(row):
            if col_idx < len(headers):
                row_dict[headers[col_idx]] = value
        rows.append(row_dict)
    
    wb.close()
    return headers, rows


def write_schedule_excel(
    filepath: str,
    original_columns: List[str],
    rows: List[Dict[str, Any]],
    sheet_name: str = "Schedule"
) -> None:
    """
    Write scheduled applicants to Excel with original columns plus scheduling fields.
    
    Args:
        filepath: Output Excel file path
        original_columns: Original column names from input
        rows: List of dicts with original + scheduling fields
        sheet_name: Name of output sheet
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # Build output columns: original + scheduling fields
    scheduling_fields = ["Music Audition Date", "Music Audition Time", "Music Audition Order"]
    output_columns = original_columns + scheduling_fields
    
    # Write header
    for col_idx, col_name in enumerate(output_columns, start=1):
        ws.cell(row=1, column=col_idx, value=col_name)
    
    # Write data rows
    for row_idx, row_data in enumerate(rows, start=2):
        for col_idx, col_name in enumerate(output_columns, start=1):
            value = row_data.get(col_name, "")
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Create parent directory if needed
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    wb.save(filepath)
    wb.close()


def write_conflicts_excel(
    filepath: str,
    conflicts: List[Dict[str, Any]],
    sheet_name: str = "Conflicts"
) -> None:
    """
    Write conflicts report to Excel.
    
    Args:
        filepath: Output Excel file path
        conflicts: List of conflict dicts with keys: ApplicantID, Degree, Discipline, ReasonCode, Details
        sheet_name: Name of output sheet
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # Define columns
    columns = ["ApplicantID", "Degree", "Discipline", "ReasonCode", "Details"]
    
    # Write header
    for col_idx, col_name in enumerate(columns, start=1):
        ws.cell(row=1, column=col_idx, value=col_name)
    
    # Write conflicts
    for row_idx, conflict in enumerate(conflicts, start=2):
        for col_idx, col_name in enumerate(columns, start=1):
            value = conflict.get(col_name, "")
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Create parent directory if needed
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    wb.save(filepath)
    wb.close()


def get_date_columns(filepath: str, sheet_name: Optional[str] = None) -> List[Any]:
    """
    Auto-detect date columns (headers that are dates or match YYYY-MM-DD pattern).
    
    Args:
        filepath: Path to Excel file
        sheet_name: Name of sheet to read (None = first sheet)
        
    Returns:
        List of column headers that appear to be dates (preserves original type)
    """
    import re
    from datetime import datetime
    
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    if sheet_name:
        ws = wb[sheet_name]
    else:
        ws = wb.active
    
    date_columns = []
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    for cell in ws[1]:
        if cell.value is None:
            continue
            
        # Check if value is datetime object - keep as datetime
        if isinstance(cell.value, datetime):
            date_columns.append(cell.value)
        # Check if string matches YYYY-MM-DD pattern
        elif isinstance(cell.value, str) and date_pattern.match(cell.value):
            date_columns.append(cell.value)
    
    wb.close()
    return date_columns


