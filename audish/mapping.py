"""
Column normalization using mapping.yaml.
Maps physical Excel column names to logical field names.
"""

from typing import Dict, Any, Optional
import yaml


class ColumnMapper:
    """Maps physical column names to logical field names."""
    
    def __init__(self, mapping_filepath: str):
        """
        Load mapping configuration from YAML file.
        
        Args:
            mapping_filepath: Path to mapping.yaml
        """
        with open(mapping_filepath, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.applicants_config = self.config.get('applicants', {})
        self.faculty_config = self.config.get('faculty', {})
        self.faculty_name_aliases = self.config.get('faculty_name_aliases', {})
    
    def get_applicant_sheet_name(self) -> str:
        """Get the sheet name for applicants."""
        return self.applicants_config.get('sheet', 'Export')
    
    def get_faculty_sheet_name(self) -> str:
        """Get the sheet name for faculty."""
        return self.faculty_config.get('sheet', 'Sheet1')
    
    def get_applicant_column(self, logical_name: str) -> Optional[str]:
        """
        Get physical column name for a logical applicant field.
        
        Args:
            logical_name: Logical field name (e.g., 'id', 'degree', 'teacher1')
            
        Returns:
            Physical column name from Excel, or None if not mapped
        """
        columns = self.applicants_config.get('columns', {})
        return columns.get(logical_name)
    
    def get_faculty_column(self, logical_name: str) -> Optional[str]:
        """
        Get physical column name for a logical faculty field.
        
        Args:
            logical_name: Logical field name (e.g., 'faculty_name', 'notes')
            
        Returns:
            Physical column name from Excel, or None if not mapped
        """
        columns = self.faculty_config.get('columns', {})
        return columns.get(logical_name)
    
    def get_faculty_name_aliases(self) -> Dict[str, str]:
        """
        Get manual faculty name aliases for edge cases.
        
        Returns:
            Dict mapping applicant teacher names to faculty sheet names
        """
        return self.faculty_name_aliases
    
    def normalize_applicant(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize an applicant row to use logical field names.
        
        Args:
            row: Raw row dict with physical column names
            
        Returns:
            Dict with logical field names
        """
        normalized = {}
        columns = self.applicants_config.get('columns', {})
        
        for logical_name, physical_name in columns.items():
            if physical_name in row:
                normalized[logical_name] = row[physical_name]
            else:
                normalized[logical_name] = None
        
        # Keep original row for preservation
        normalized['_original'] = row
        
        return normalized
    
    def normalize_faculty(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a faculty row to use logical field names.
        
        Args:
            row: Raw row dict with physical column names
            
        Returns:
            Dict with logical field names
        """
        normalized = {}
        columns = self.faculty_config.get('columns', {})
        
        for logical_name, physical_name in columns.items():
            if physical_name in row:
                normalized[logical_name] = row[physical_name]
            else:
                normalized[logical_name] = None
        
        # Keep original row
        normalized['_original'] = row
        
        return normalized
    
    def denormalize_applicant(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert normalized applicant back to physical column names.
        
        Args:
            normalized: Dict with logical field names
            
        Returns:
            Dict with physical column names
        """
        # Start with original row if available
        if '_original' in normalized:
            physical = dict(normalized['_original'])
        else:
            physical = {}
        
        # Map logical names back to physical
        columns = self.applicants_config.get('columns', {})
        for logical_name, physical_name in columns.items():
            if logical_name in normalized and logical_name != '_original':
                physical[physical_name] = normalized[logical_name]
        
        return physical


def normalize_degree(degree: Optional[str]) -> Optional[str]:
    """
    Normalize degree values to standard codes.
    
    Args:
        degree: Raw degree string from input
        
    Returns:
        Normalized degree code (BM/MM/GD/AD/DMA/BCJ) or None
    """
    if not degree:
        return None
    
    degree_upper = str(degree).strip().upper()
    
    # Handle common variations
    if degree_upper in ['BM', 'BACHELOR OF MUSIC']:
        return 'BM'
    elif degree_upper in ['MM', 'MASTER OF MUSIC']:
        return 'MM'
    elif degree_upper in ['GD', 'GRADUATE DIPLOMA']:
        return 'GD'
    elif degree_upper in ['AD', 'ARTIST DIPLOMA']:
        return 'AD'
    elif degree_upper in ['DMA', 'DOCTOR OF MUSICAL ARTS']:
        return 'DMA'
    elif degree_upper in ['BCJ', 'BACHELOR OF JAZZ']:
        return 'BCJ'
    
    # Return as-is if no match
    return degree_upper


