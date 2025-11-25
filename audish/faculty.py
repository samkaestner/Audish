"""
Faculty availability parsing.
Auto-detects date columns and parses Notes grammar.
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, time
import re


def parse_time(time_str: str) -> Optional[time]:
    """
    Parse a time string to a time object.
    Supports formats: "1pm", "13:00", "1:00pm", "13"
    
    Args:
        time_str: Time string
        
    Returns:
        time object or None if parsing fails
    """
    time_str = time_str.strip().lower()
    
    # Try HH:MM format (24-hour)
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    # Try HH:MMam/pm format
    match = re.match(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', time_str)
    if match:
        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    # Try Hpm/Ham format
    match = re.match(r'^(\d{1,2})\s*(am|pm)$', time_str)
    if match:
        hour, period = int(match.group(1)), match.group(2)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            return time(hour, 0)
    
    # Try just hour (assume 24-hour)
    match = re.match(r'^(\d{1,2})$', time_str)
    if match:
        hour = int(match.group(1))
        if 0 <= hour <= 23:
            return time(hour, 0)
    
    return None


def parse_notes(notes: Optional[str]) -> Dict[str, Any]:
    """
    Parse faculty Notes field for time constraints.
    
    Supports:
    - "after 1pm" / "after 13:00" → lower bound
    - "before 2pm" → upper bound
    - "10:00–14:00" / "10:00-14:00" → window
    - "not Friday" / "no Fri" → exclude day
    - "except 3/1" → exclude specific date
    
    Args:
        notes: Notes text from faculty row
        
    Returns:
        Dict with parsed constraints:
        {
            'after': time object or None,
            'before': time object or None,
            'window': (start_time, end_time) or None,
            'exclude_days': list of day names,
            'exclude_dates': list of date strings (M/D format)
        }
    """
    result = {
        'after': None,
        'before': None,
        'window': None,
        'exclude_days': [],
        'exclude_dates': []
    }
    
    if not notes:
        return result
    
    notes_lower = notes.lower()
    
    # Parse "after HH:MM" or "after Hpm"
    match = re.search(r'after\s+([0-9:apm\s]+)', notes_lower)
    if match:
        time_obj = parse_time(match.group(1))
        if time_obj:
            result['after'] = time_obj
    
    # Parse "before HH:MM" or "before Hpm"
    match = re.search(r'before\s+([0-9:apm\s]+)', notes_lower)
    if match:
        time_obj = parse_time(match.group(1))
        if time_obj:
            result['before'] = time_obj
    
    # Parse time window "HH:MM–HH:MM" or "HH:MM-HH:MM"
    match = re.search(r'(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})', notes)
    if match:
        start_time = parse_time(match.group(1))
        end_time = parse_time(match.group(2))
        if start_time and end_time:
            result['window'] = (start_time, end_time)
    
    # Parse "not Friday" / "no Friday" / "no Fri"
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    for day in day_names:
        if re.search(rf'\b(not|no)\s+{day}\b', notes_lower):
            # Normalize to full day name
            day_map = {
                'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
                'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
            }
            full_day = day_map.get(day, day)
            if full_day not in result['exclude_days']:
                result['exclude_days'].append(full_day)
    
    # Parse "except M/D"
    match = re.search(r'except\s+(\d{1,2}/\d{1,2})', notes_lower)
    if match:
        result['exclude_dates'].append(match.group(1))
    
    return result


def build_faculty_availability(
    faculty_rows: List[Dict[str, Any]],
    date_columns: List[str],
    faculty_name_col: str,
    notes_col: str,
    calendar_days: List[Dict[str, Any]]
) -> Dict[str, Dict[str, List[Tuple[time, time]]]]:
    """
    Build faculty availability map from faculty Excel data.
    
    Args:
        faculty_rows: List of normalized faculty row dicts
        date_columns: List of date column names (YYYY-MM-DD format)
        faculty_name_col: Logical name for faculty name column
        notes_col: Logical name for notes column
        calendar_days: List of calendar day dicts from rules.yaml with 'date', 'start', 'end'
        
    Returns:
        Nested dict: {faculty_name: {date_str: [(start_time, end_time), ...]}}
    """
    availability = {}
    
    # Build calendar lookup - handle both string, date, and datetime objects
    calendar_lookup = {}
    for day in calendar_days:
        day_date = day['date']
        start_time = parse_time(day['start']) or time(9, 0)
        end_time = parse_time(day['end']) or time(17, 0)
        
        # Normalize to string for consistent lookup
        if isinstance(day_date, str):
            date_str = day_date
        elif isinstance(day_date, datetime):
            date_str = day_date.strftime('%Y-%m-%d')
        else:
            # date object
            date_str = day_date.strftime('%Y-%m-%d')
        
        # Store with multiple key formats for flexible lookup
        calendar_lookup[date_str] = (start_time, end_time)  # String: "2025-03-04"
        
        # Also store with datetime/date objects that might come from Excel
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            calendar_lookup[date_obj] = (start_time, end_time)  # date(2025, 3, 4)
            datetime_obj = datetime.strptime(date_str, '%Y-%m-%d')
            calendar_lookup[datetime_obj] = (start_time, end_time)  # datetime(2025, 3, 4, 0, 0)
        except ValueError:
            pass
    
    for row in faculty_rows:
        faculty_name = row.get(faculty_name_col)
        if not faculty_name:
            continue
        
        # Parse notes constraints
        notes = row.get(notes_col)
        constraints = parse_notes(notes)
        
        availability[faculty_name] = {}
        
        # Check each date column
        for date_col in date_columns:
            # Get cell value from original row
            original_row = row.get('_original', {})
            cell_value = original_row.get(date_col)
            
            # Skip if not present or explicitly marked as unavailable
            # Common values: None, '', 'n', 'N', 'no', 'No', 'N/A'
            if cell_value in [None, '']:
                continue
            
            # Check for "no" indicators (case-insensitive)
            cell_str = str(cell_value).strip().lower()
            if cell_str in ['n', 'no', 'n/a', 'na', 'not available', 'unavailable']:
                continue
            
            # Get base calendar hours for this date
            # date_col might be a string or datetime object
            if date_col not in calendar_lookup:
                continue
            
            cal_start, cal_end = calendar_lookup[date_col]
            
            # Parse date to check day of week
            if isinstance(date_col, datetime):
                date_obj = date_col
                date_str = date_col.strftime('%Y-%m-%d')
            elif isinstance(date_col, str):
                try:
                    date_obj = datetime.strptime(date_col, '%Y-%m-%d')
                    date_str = date_col
                except ValueError:
                    continue
            else:
                continue
            
            day_name = date_obj.strftime('%A').lower()
            
            # Check exclude_days constraint
            if day_name in constraints['exclude_days']:
                continue
            
            # Check exclude_dates constraint (M/D format)
            date_md = f"{date_obj.month}/{date_obj.day}"
            if date_md in constraints['exclude_dates']:
                continue
            
            # Determine time window for this date
            if constraints['window']:
                # Explicit time window from notes
                start_time, end_time = constraints['window']
            elif constraints['after'] or constraints['before']:
                # After/before constraints
                start_time = constraints['after'] or cal_start
                end_time = constraints['before'] or cal_end
            else:
                # Use calendar default
                start_time, end_time = cal_start, cal_end
            
            # Store availability window (use string date for consistency)
            availability[faculty_name][date_str] = [(start_time, end_time)]
    
    return availability


def is_faculty_available(
    faculty_name: str,
    date_str: str,
    slot_start: datetime,
    availability: Dict[str, Dict[str, List[Tuple[time, time]]]]
) -> bool:
    """
    Check if a faculty member is available for a specific slot.
    
    Args:
        faculty_name: Name of faculty member
        date_str: Date string (YYYY-MM-DD)
        slot_start: Slot start datetime
        availability: Faculty availability map from build_faculty_availability
        
    Returns:
        True if faculty is available, False otherwise
    """
    if faculty_name not in availability:
        return False
    
    if date_str not in availability[faculty_name]:
        return False
    
    slot_time = slot_start.time()
    
    for start_time, end_time in availability[faculty_name][date_str]:
        if start_time <= slot_time < end_time:
            return True
    
    return False


