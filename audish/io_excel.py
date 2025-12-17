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
        
    Note:
        If the specified sheet name isn't found but the workbook only has one sheet,
        that sheet is used automatically. This handles the common case where users
        copy/paste data into a new workbook (which defaults to "Sheet1").
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    if sheet_name:
        if sheet_name not in wb.sheetnames:
            # If there's only one sheet, use it regardless of name
            # This handles copy/paste into new workbook scenarios
            if len(wb.sheetnames) == 1:
                ws = wb.active
            else:
                raise ValueError(
                    f"Sheet '{sheet_name}' not found in {filepath}. "
                    f"Available sheets: {wb.sheetnames}"
                )
        else:
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
    
    # Build output columns: use original_columns as-is
    # The format_scheduled_output function handles filling in existing audition columns
    # and only adds new columns if they don't exist
    output_columns = original_columns
    
    # Check if any scheduling fields need to be added (they're in the row dict but not in columns)
    scheduling_fields = ["Music Audition Date", "Music Audition Time", "Music Audition Order"]
    if rows:
        # Check first row to see if it has any scheduling fields not in original_columns
        first_row = rows[0]
        for field in scheduling_fields:
            if field in first_row and field not in output_columns:
                output_columns.append(field)
    
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
    
    # Delete existing file if it exists to ensure clean overwrite
    # This prevents issues with locked files or permission problems
    filepath_obj = Path(filepath)
    if filepath_obj.exists():
        try:
            filepath_obj.unlink()
        except Exception as e:
            # If we can't delete, try to overwrite anyway
            print(f"Warning: Could not delete existing file {filepath}: {e}")
    
    wb.save(filepath)
    wb.close()


def write_conflicts_excel(
    filepath: str,
    conflicts: List[Dict[str, Any]],
    original_columns: Optional[List[str]] = None,
    sheet_name: str = "Conflicts"
) -> None:
    """
    Write conflicts report to Excel.
    
    Preserves all original identifying fields from the input data, making it
    easier to understand why each applicant was excluded.
    
    Args:
        filepath: Output Excel file path
        conflicts: List of conflict dicts containing original applicant data plus conflict fields
        original_columns: Original column names from input (preserves order). If None, auto-detects.
        sheet_name: Name of output sheet
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    if not conflicts:
        # Write empty file with just conflict headers
        columns = ["ReasonCode", "ConflictDetails"]
        for col_idx, col_name in enumerate(columns, start=1):
            ws.cell(row=1, column=col_idx, value=col_name)
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Delete existing file if it exists to ensure clean overwrite
        filepath_obj = Path(filepath)
        if filepath_obj.exists():
            try:
                filepath_obj.unlink()
            except Exception as e:
                # If we can't delete, try to overwrite anyway
                print(f"Warning: Could not delete existing file {filepath}: {e}")
        
        wb.save(filepath)
        wb.close()
        return
    
    # Build column list: original columns first, then conflict-specific fields at the end
    # Conflict-specific fields are prefixed with _ to distinguish them
    conflict_fields = ['_ReasonCode', '_ConflictDetails', '_Discipline']
    
    if original_columns:
        # Use the original column order, filtering out conflict-specific fields
        columns = [col for col in original_columns if not col.startswith('_')]
    else:
        # Auto-detect columns from first conflict record (excluding internal fields)
        columns = [k for k in conflicts[0].keys() if not k.startswith('_')]
    
    # Add conflict-specific fields at the end with friendly names
    output_columns = columns + ['Reason Code', 'Conflict Details', 'Discipline']
    
    # Map from output column name to source key
    column_source_map = {col: col for col in columns}
    column_source_map['Reason Code'] = '_ReasonCode'
    column_source_map['Conflict Details'] = '_ConflictDetails'
    column_source_map['Discipline'] = '_Discipline'
    
    # Write header
    for col_idx, col_name in enumerate(output_columns, start=1):
        ws.cell(row=1, column=col_idx, value=col_name)
    
    # Write conflicts
    for row_idx, conflict in enumerate(conflicts, start=2):
        for col_idx, col_name in enumerate(output_columns, start=1):
            source_key = column_source_map.get(col_name, col_name)
            value = conflict.get(source_key, "")
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Create parent directory if needed
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Delete existing file if it exists to ensure clean overwrite
    # This prevents issues with locked files or permission problems
    filepath_obj = Path(filepath)
    if filepath_obj.exists():
        try:
            filepath_obj.unlink()
        except Exception as e:
            # If we can't delete, try to overwrite anyway
            print(f"Warning: Could not delete existing file {filepath}: {e}")
    
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
        
    Note:
        If the specified sheet name isn't found but the workbook only has one sheet,
        that sheet is used automatically.
    """
    import re
    from datetime import datetime
    
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    if sheet_name:
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        elif len(wb.sheetnames) == 1:
            # Use the only available sheet
            ws = wb.active
        else:
            ws = wb[sheet_name]  # This will raise KeyError with available sheets
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


