"""
Faculty name normalization and matching utilities.
Handles differences between Faculty Availability and Applicant teacher names.
"""

import re
from typing import Dict, Optional, Set


# Common academic and professional titles to strip
COMMON_TITLES = [
    'dr.', 'dr', 'doctor',
    'prof.', 'prof', 'professor',
    'mr.', 'mr', 'mister',
    'ms.', 'ms',
    'mrs.', 'mrs',
    'miss',
    'mx.',
    'sir',
    'dame',
    'rev.', 'reverend',
    'hon.', 'honorable',
]


def normalize_name(name: Optional[str]) -> str:
    """
    Normalize a faculty name for matching.
    
    Steps:
    1. Convert to lowercase
    2. Remove titles (Dr., Prof., Mr., Ms., etc.)
    3. Remove extra whitespace
    4. Remove punctuation
    
    Args:
        name: Raw faculty name
        
    Returns:
        Normalized name for matching
        
    Examples:
        "Dr. John Smith" -> "john smith"
        "Jane Doe" -> "jane doe"
        "Prof. Mary-Anne O'Brien" -> "mary anne obrien"
    """
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove titles (word boundaries to avoid matching parts of names)
    for title in COMMON_TITLES:
        # Match title at start of string with optional punctuation and space
        pattern = rf'\b{re.escape(title)}\s+'
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    # Remove punctuation except spaces and hyphens (keep hyphenated names initially)
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    # Normalize hyphens and apostrophes to spaces
    normalized = re.sub(r'[-]', ' ', normalized)
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def build_faculty_name_map(
    faculty_names: Set[str],
    aliases: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Build a mapping from normalized names to original faculty names.
    
    Args:
        faculty_names: Set of original faculty names from Faculty sheet
        aliases: Optional dict of manual name mappings from mapping.yaml
                 Format: {"applicant_teacher_name": "faculty_sheet_name"}
        
    Returns:
        Dict mapping normalized names to original faculty names
        
    Example:
        faculty_names = {"John Smith", "Jane Doe"}
        Returns: {
            "john smith": "John Smith",
            "jane doe": "Jane Doe"
        }
    """
    name_map = {}
    
    # Add normalized faculty names
    for faculty_name in faculty_names:
        normalized = normalize_name(faculty_name)
        if normalized:
            name_map[normalized] = faculty_name
    
    # Add manual aliases if provided
    if aliases:
        for applicant_name, faculty_name in aliases.items():
            normalized_applicant = normalize_name(applicant_name)
            if normalized_applicant and faculty_name in faculty_names:
                name_map[normalized_applicant] = faculty_name
    
    return name_map


def match_teacher_name(
    teacher_name: Optional[str],
    faculty_name_map: Dict[str, str]
) -> Optional[str]:
    """
    Match a teacher name from applicant data to a faculty member.
    
    Args:
        teacher_name: Teacher name from applicant (e.g., "Dr. John Smith")
        faculty_name_map: Normalized name to faculty name mapping
        
    Returns:
        Matched faculty name or None if no match
        
    Examples:
        teacher_name = "Dr. John Smith"
        faculty_name_map = {"john smith": "John Smith"}
        Returns: "John Smith"
    """
    if not teacher_name:
        return None
    
    normalized = normalize_name(teacher_name)
    return faculty_name_map.get(normalized)


def get_all_faculty_names(faculty_records: list, faculty_name_col: str) -> Set[str]:
    """
    Extract all unique faculty names from faculty records.
    
    Args:
        faculty_records: List of normalized faculty dicts
        faculty_name_col: Column name for faculty name
        
    Returns:
        Set of unique faculty names
    """
    names = set()
    for record in faculty_records:
        name = record.get(faculty_name_col)
        if name:
            names.add(name)
    return names


def diagnose_teacher_matching(
    applicants: list,
    faculty_name_map: Dict[str, str],
    teacher_cols: list = ['teacher1', 'teacher2', 'teacher3']
) -> Dict[str, any]:
    """
    Analyze teacher name matching for diagnostics.
    
    Args:
        applicants: List of normalized applicant dicts
        faculty_name_map: Name mapping
        teacher_cols: Teacher column names to check
        
    Returns:
        Dict with matching statistics
    """
    stats = {
        'total_teacher_preferences': 0,
        'matched': 0,
        'unmatched': 0,
        'unmatched_names': set()
    }
    
    for applicant in applicants:
        for col in teacher_cols:
            teacher_name = applicant.get(col)
            if teacher_name:
                stats['total_teacher_preferences'] += 1
                matched = match_teacher_name(teacher_name, faculty_name_map)
                if matched:
                    stats['matched'] += 1
                else:
                    stats['unmatched'] += 1
                    stats['unmatched_names'].add(teacher_name)
    
    stats['match_rate'] = (stats['matched'] / stats['total_teacher_preferences'] * 100) if stats['total_teacher_preferences'] > 0 else 0
    
    return stats




