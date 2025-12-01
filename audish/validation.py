"""
Configuration validation with helpful error messages.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class ValidationError(Exception):
    """Raised when configuration is invalid with helpful context."""
    pass


def validate_mapping_file(mapping_path: str, app_path: str, fac_path: str) -> List[str]:
    """
    Validate mapping.yaml against actual Excel files.
    
    Returns list of warnings (non-fatal issues).
    Raises ValidationError for fatal problems.
    """
    warnings = []
    
    # Load mapping
    with open(mapping_path) as f:
        config = yaml.safe_load(f)
    
    # Check structure
    if 'applicants' not in config:
        raise ValidationError(
            f"❌ Configuration Error in {mapping_path}\n\n"
            f"Missing required section: 'applicants'\n\n"
            f"Fix: Add this to your mapping.yaml:\n"
            f"applicants:\n"
            f"  sheet: \"Export\"\n"
            f"  columns:\n"
            f"    id: \"Application Slate ID\"\n"
            f"    # ... more columns"
        )
    
    if 'faculty' not in config:
        raise ValidationError(
            f"❌ Configuration Error in {mapping_path}\n\n"
            f"Missing required section: 'faculty'\n\n"
            f"Fix: Add this to your mapping.yaml:\n"
            f"faculty:\n"
            f"  sheet: \"Sheet1\"\n"
            f"  columns:\n"
            f"    faculty_name: \"Faculty\"\n"
            f"    # ... more columns"
        )
    
    # Validate applicant sheet exists
    app_sheet = config['applicants'].get('sheet')
    if not app_sheet:
        raise ValidationError(
            f"❌ Configuration Error in {mapping_path}\n\n"
            f"Missing 'sheet' in applicants section\n\n"
            f"Fix: Add sheet name:\n"
            f"applicants:\n"
            f"  sheet: \"Export\"  # <-- Add this"
        )
    
    # Check if sheet exists in Excel file
    from openpyxl import load_workbook
    try:
        wb = load_workbook(app_path, read_only=True, data_only=True)
        available_sheets = wb.sheetnames
        wb.close()
        
        if app_sheet not in available_sheets:
            # Try to suggest similar sheet name
            from difflib import get_close_matches
            suggestions = get_close_matches(app_sheet, available_sheets, n=1, cutoff=0.6)
            
            error_msg = (
                f"❌ Configuration Error in {mapping_path}\n\n"
                f"Sheet '{app_sheet}' not found in {Path(app_path).name}\n"
                f"Available sheets: {', '.join(available_sheets)}\n\n"
            )
            
            if suggestions:
                error_msg += f"Did you mean '{suggestions[0]}'?\n\n"
            
            error_msg += (
                f"Fix: Change mapping.yaml line 2 to:\n"
                f"  sheet: \"{available_sheets[0]}\"  # <-- Use exact name"
            )
            
            raise ValidationError(error_msg)
            
    except FileNotFoundError:
        raise ValidationError(
            f"❌ File Not Found\n\n"
            f"Could not open: {app_path}\n\n"
            f"Make sure the file path is correct."
        )
    
    # Check required columns
    required_app_columns = ['id', 'degree', 'major']
    app_columns = config['applicants'].get('columns', {})
    
    missing = [col for col in required_app_columns if col not in app_columns]
    if missing:
        raise ValidationError(
            f"❌ Configuration Error in {mapping_path}\n\n"
            f"Missing required applicant columns: {', '.join(missing)}\n\n"
            f"Fix: Add to applicants.columns section:\n" +
            '\n'.join(f"  {col}: \"Column Name From Excel\"" for col in missing)
        )
    
    return warnings


def validate_rules_file(rules_path: str, applicants: List[Dict]) -> List[str]:
    """
    Validate rules.yaml against actual applicant data.
    
    Returns list of warnings.
    Raises ValidationError for fatal problems.
    """
    warnings = []
    
    # Load rules
    with open(rules_path) as f:
        config = yaml.safe_load(f)
    
    # Get unique discipline/degree combinations from applicants
    actual_combos = set()
    for app in applicants:
        discipline = app.get('major') or app.get('department')
        degree = app.get('degree')
        if discipline and degree:
            actual_combos.add((discipline, degree))
    
    # Check if rules exist for each combo
    rules = config.get('rules', {})
    
    missing_rules = []
    for discipline, degree in actual_combos:
        if discipline not in rules:
            missing_rules.append((discipline, degree, 'discipline'))
        elif degree not in rules[discipline] and 'ALL' not in rules[discipline]:
            missing_rules.append((discipline, degree, 'degree'))
    
    if missing_rules:
        # Count affected applicants
        affected = defaultdict(int)
        for app in applicants:
            disc = app.get('major') or app.get('department')
            deg = app.get('degree')
            if any(disc == d and deg == dg for d, dg, _ in missing_rules):
                affected[(disc, deg)] += 1
        
        error_msg = f"❌ Configuration Error in {rules_path}\n\n"
        error_msg += "Missing scheduling rules for:\n\n"
        
        for discipline, degree, missing_type in missing_rules[:5]:  # Show first 5
            count = affected.get((discipline, degree), 0)
            error_msg += f"  • {discipline} - {degree} ({count} applicants)\n"
        
        if len(missing_rules) > 5:
            error_msg += f"  • ... and {len(missing_rules) - 5} more\n"
        
        error_msg += "\nFix: Add rules to rules.yaml:\n\n"
        
        for discipline, degree, _ in list(missing_rules)[:3]:  # Show fix for first 3
            error_msg += f"  {discipline}:\n"
            error_msg += f"    {degree}: {{ cadence: {{ type: fixed_interval, minutes: 15 }} }}\n"
        
        raise ValidationError(error_msg)
    
    return warnings