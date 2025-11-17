"""
Tests for faculty name normalization and matching.
"""

import pytest

from audish.faculty_names import normalize_name, build_faculty_name_map, match_teacher_name


class TestNormalizeName:
    """Test name normalization."""
    
    def test_simple_name(self):
        assert normalize_name("John Smith") == "john smith"
        assert normalize_name("Jane Doe") == "jane doe"
    
    def test_title_removal(self):
        assert normalize_name("Dr. John Smith") == "john smith"
        assert normalize_name("Prof. Jane Doe") == "jane doe"
        assert normalize_name("Mr. Bob Johnson") == "bob johnson"
        assert normalize_name("Ms. Mary Wilson") == "mary wilson"
        assert normalize_name("Mrs. Susan Brown") == "susan brown"
    
    def test_title_with_no_period(self):
        assert normalize_name("Dr John Smith") == "john smith"
        assert normalize_name("Professor Jane Doe") == "jane doe"
    
    def test_hyphenated_names(self):
        assert normalize_name("Mary-Anne Johnson") == "mary anne johnson"
        assert normalize_name("Jean-Pierre Rampal") == "jean pierre rampal"
    
    def test_apostrophes(self):
        assert normalize_name("O'Brien") == "obrien"
        assert normalize_name("Mary O'Connor") == "mary oconnor"
    
    def test_multiple_titles(self):
        assert normalize_name("Dr. Prof. John Smith") == "john smith"
    
    def test_empty_and_none(self):
        assert normalize_name(None) == ""
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""
    
    def test_extra_whitespace(self):
        assert normalize_name("  John   Smith  ") == "john smith"
        assert normalize_name("Dr.    John    Smith") == "john smith"


class TestBuildFacultyNameMap:
    """Test building faculty name mapping."""
    
    def test_basic_mapping(self):
        faculty_names = {"John Smith", "Jane Doe", "Bob Johnson"}
        name_map = build_faculty_name_map(faculty_names)
        
        assert name_map["john smith"] == "John Smith"
        assert name_map["jane doe"] == "Jane Doe"
        assert name_map["bob johnson"] == "Bob Johnson"
    
    def test_with_aliases(self):
        faculty_names = {"John Smith", "Jane Doe"}
        aliases = {
            "Dr. John Smith": "John Smith",
            "Professor Jane Doe": "Jane Doe"
        }
        name_map = build_faculty_name_map(faculty_names, aliases)
        
        # Both normalized names should map to the same faculty
        assert name_map["john smith"] == "John Smith"
        assert name_map["jane doe"] == "Jane Doe"
    
    def test_empty_names_ignored(self):
        faculty_names = {"John Smith", "", None, "Jane Doe"}
        name_map = build_faculty_name_map(faculty_names)
        
        assert "john smith" in name_map
        assert "jane doe" in name_map
        assert "" not in name_map


class TestMatchTeacherName:
    """Test teacher name matching."""
    
    def test_exact_match(self):
        faculty_name_map = {
            "john smith": "John Smith",
            "jane doe": "Jane Doe"
        }
        
        assert match_teacher_name("John Smith", faculty_name_map) == "John Smith"
        assert match_teacher_name("Jane Doe", faculty_name_map) == "Jane Doe"
    
    def test_match_with_title(self):
        faculty_name_map = {
            "john smith": "John Smith",
            "jane doe": "Jane Doe"
        }
        
        # Applicant data has titles, faculty sheet doesn't
        assert match_teacher_name("Dr. John Smith", faculty_name_map) == "John Smith"
        assert match_teacher_name("Prof. Jane Doe", faculty_name_map) == "Jane Doe"
        assert match_teacher_name("Mr. John Smith", faculty_name_map) == "John Smith"
    
    def test_no_match(self):
        faculty_name_map = {
            "john smith": "John Smith"
        }
        
        assert match_teacher_name("Jane Doe", faculty_name_map) is None
        assert match_teacher_name("Bob Johnson", faculty_name_map) is None
    
    def test_none_teacher_name(self):
        faculty_name_map = {"john smith": "John Smith"}
        
        assert match_teacher_name(None, faculty_name_map) is None
        assert match_teacher_name("", faculty_name_map) is None
    
    def test_case_insensitive(self):
        faculty_name_map = {
            "john smith": "John Smith"
        }
        
        assert match_teacher_name("JOHN SMITH", faculty_name_map) == "John Smith"
        assert match_teacher_name("john smith", faculty_name_map) == "John Smith"
        assert match_teacher_name("Dr. JOHN SMITH", faculty_name_map) == "John Smith"
    
    def test_hyphenated_and_apostrophe(self):
        faculty_name_map = {
            "mary anne johnson": "Mary-Anne Johnson",
            "jean pierre rampal": "Jean-Pierre Rampal",
            "mary oconnor": "Mary O'Connor"
        }
        
        # Test that different representations match
        assert match_teacher_name("Mary-Anne Johnson", faculty_name_map) == "Mary-Anne Johnson"
        assert match_teacher_name("Dr. Jean-Pierre Rampal", faculty_name_map) == "Jean-Pierre Rampal"
        assert match_teacher_name("Mary O'Connor", faculty_name_map) == "Mary O'Connor"



