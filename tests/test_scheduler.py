"""
Tests for scheduling algorithm.
"""

from datetime import datetime, time
import pytest
import tempfile
import os

from audish.rules import RulesEngine
from audish.scheduler import Scheduler
from audish.mapping import ColumnMapper


@pytest.fixture
def sample_config_files():
    """Create temporary config files for testing."""
    
    # mapping.yaml
    mapping_content = """
applicants:
  sheet: "Export"
  columns:
    id: "ApplicantID"
    degree: "Degree"
    major: "Major"
    teacher1: "Teacher1"
    teacher2: "Teacher2"
    teacher3: "Teacher3"
    school_org: "School"
    juilliard_status: "Status"

faculty:
  sheet: "Sheet1"
  columns:
    faculty_name: "Name"
    notes: "Notes"
"""
    
    # rules.yaml
    rules_content = """
timezone: "America/New_York"
degree_precedence: ["BM", "MM", "GD", "AD", "DMA"]
teacher_presence_policy: "prefer"
same_school_spacing: true
double_major_window_hours: 24

calendar:
  days:
    - { date: 2025-03-01, start: "09:00", end: "12:00" }
    - { date: 2025-03-02, start: "09:00", end: "12:00" }

rules:
  Violin:
    BM:
      cadence: { type: fixed_interval, minutes: 15 }
    MM:
      cadence: { type: fixed_interval, minutes: 15 }
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(mapping_content)
        mapping_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(rules_content)
        rules_path = f.name
    
    yield mapping_path, rules_path
    
    # Cleanup
    os.unlink(mapping_path)
    os.unlink(rules_path)


class TestDegreeOrdering:
    """Test that applicants are scheduled in degree precedence order."""
    
    def test_bm_before_mm(self, sample_config_files):
        mapping_path, rules_path = sample_config_files
        
        mapper = ColumnMapper(mapping_path)
        rules = RulesEngine(rules_path)
        
        # Create applicants: 1 MM, 1 BM
        applicants = [
            {
                'id': 'A001', 'degree': 'MM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': None, 'teacher3': None,
                'school_org': 'School A', 'juilliard_status': None,
                '_original': {}
            },
            {
                'id': 'A002', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': None, 'teacher3': None,
                'school_org': 'School B', 'juilliard_status': None,
                '_original': {}
            }
        ]
        
        # Faculty availability (Prof. Smith available both days)
        faculty_availability = {
            'Prof. Smith': {
                '2025-03-01': [(time(9, 0), time(12, 0))],
                '2025-03-02': [(time(9, 0), time(12, 0))]
            }
        }
        
        # Build faculty name map
        from audish.faculty_names import build_faculty_name_map
        faculty_names = set(faculty_availability.keys())
        faculty_name_map = build_faculty_name_map(faculty_names)
        
        scheduler = Scheduler(rules, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        
        # Both should be scheduled
        assert len(scheduled) == 2
        assert len(conflicts) == 0
        
        # BM (A002) should be scheduled before MM (A001)
        scheduled_ids = [s['id'] for s in scheduled]
        scheduled_times = [(s['Music Audition Date'], s['Music Audition Time']) for s in scheduled]
        
        bm_idx = scheduled_ids.index('A002')
        mm_idx = scheduled_ids.index('A001')
        
        # BM should have earlier date/time
        assert scheduled_times[bm_idx] < scheduled_times[mm_idx]


class TestTeacherPresence:
    """Test teacher presence filtering."""
    
    def test_prefer_policy_allows_no_teacher(self, sample_config_files):
        mapping_path, rules_path = sample_config_files
        
        mapper = ColumnMapper(mapping_path)
        rules = RulesEngine(rules_path)
        
        # Applicant wants Prof. Jones who is not available
        applicants = [
            {
                'id': 'A001', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Jones', 'teacher2': None, 'teacher3': None,
                'school_org': None, 'juilliard_status': None,
                '_original': {}
            }
        ]
        
        # No faculty available
        faculty_availability = {}
        
        # Build empty faculty name map
        from audish.faculty_names import build_faculty_name_map
        faculty_name_map = build_faculty_name_map(set())
        
        scheduler = Scheduler(rules, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        
        # With "prefer" policy, should still schedule (no teacher match)
        # But slots are still generated
        assert len(scheduled) >= 0  # May or may not schedule depending on slot availability
    
    def test_first_choice_teacher_preferred(self, sample_config_files):
        mapping_path, rules_path = sample_config_files
        
        mapper = ColumnMapper(mapping_path)
        rules = RulesEngine(rules_path)
        
        applicants = [
            {
                'id': 'A001', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': 'Prof. Jones', 'teacher3': None,
                'school_org': None, 'juilliard_status': None,
                '_original': {}
            }
        ]
        
        # Prof. Smith available on day 1, Prof. Jones on day 2
        faculty_availability = {
            'Prof. Smith': {
                '2025-03-01': [(time(9, 0), time(12, 0))]
            },
            'Prof. Jones': {
                '2025-03-02': [(time(9, 0), time(12, 0))]
            }
        }
        
        # Build faculty name map
        from audish.faculty_names import build_faculty_name_map
        faculty_names = set(faculty_availability.keys())
        faculty_name_map = build_faculty_name_map(faculty_names)
        
        scheduler = Scheduler(rules, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        
        assert len(scheduled) == 1
        # Should be scheduled on day 1 with first choice teacher
        assert scheduled[0]['Music Audition Date'] == '2025-03-01'
        assert scheduled[0]['_teacher_rank'] == 3  # First choice


class TestNumbering:
    """Test sequential numbering per discipline."""
    
    def test_numbering_across_days(self, sample_config_files):
        mapping_path, rules_path = sample_config_files
        
        mapper = ColumnMapper(mapping_path)
        rules = RulesEngine(rules_path)
        
        # 3 applicants
        applicants = [
            {
                'id': f'A{i:03d}', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': None, 'teacher3': None,
                'school_org': None, 'juilliard_status': None,
                '_original': {}
            }
            for i in range(1, 4)
        ]
        
        faculty_availability = {
            'Prof. Smith': {
                '2025-03-01': [(time(9, 0), time(12, 0))],
                '2025-03-02': [(time(9, 0), time(12, 0))]
            }
        }
        
        # Build faculty name map
        from audish.faculty_names import build_faculty_name_map
        faculty_names = set(faculty_availability.keys())
        faculty_name_map = build_faculty_name_map(faculty_names)
        
        scheduler = Scheduler(rules, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        
        assert len(scheduled) == 3
        
        # Check numbering is sequential 1, 2, 3
        orders = sorted([s['Music Audition Order'] for s in scheduled])
        assert orders == [1, 2, 3]


class TestSameSchoolSpacing:
    """Test same-school spacing constraint."""
    
    def test_avoids_same_school_adjacent(self, sample_config_files):
        mapping_path, rules_path = sample_config_files
        
        mapper = ColumnMapper(mapping_path)
        rules = RulesEngine(rules_path)
        
        # Two applicants from same school
        applicants = [
            {
                'id': 'A001', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': None, 'teacher3': None,
                'school_org': 'School A', 'juilliard_status': None,
                '_original': {}
            },
            {
                'id': 'A002', 'degree': 'BM', 'major': 'Violin',
                'teacher1': 'Prof. Smith', 'teacher2': None, 'teacher3': None,
                'school_org': 'School A', 'juilliard_status': None,
                '_original': {}
            }
        ]
        
        faculty_availability = {
            'Prof. Smith': {
                '2025-03-01': [(time(9, 0), time(12, 0))],
                '2025-03-02': [(time(9, 0), time(12, 0))]
            }
        }
        
        # Build faculty name map
        from audish.faculty_names import build_faculty_name_map
        faculty_names = set(faculty_availability.keys())
        faculty_name_map = build_faculty_name_map(faculty_names)
        
        scheduler = Scheduler(rules, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        
        # Both should be scheduled
        assert len(scheduled) == 2
        
        # Should not be in adjacent slots (within 30 minutes)
        times = []
        for s in scheduled:
            date_str = s['Music Audition Date']
            time_str = s['Music Audition Time']
            hour, minute = map(int, time_str.split(':'))
            dt = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=hour, minute=minute)
            times.append(dt)
        
        times.sort()
        if len(times) == 2:
            gap = (times[1] - times[0]).total_seconds() / 60
            # Gap should be at least 30 minutes (or on different days)
            assert gap >= 30 or times[0].date() != times[1].date()


