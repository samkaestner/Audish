"""
Tests for per-discipline start/end time overrides.
"""

from datetime import datetime, time
import pytest
import tempfile
import os

from audish.rules import RulesEngine


@pytest.fixture
def discipline_time_config():
    """Create temporary config file with per-discipline time overrides."""
    
    rules_content = """
timezone: "America/New_York"
degree_precedence: ["BM", "MM"]

calendar:
  days:
    - { date: 2025-03-01, start: "09:00", end: "17:00" }  # Default calendar times

rules:
  Violin:
    start_time: "10:00"  # Override start time for all Violin auditions
    end_time: "18:00"    # Override end time for all Violin auditions
    ALL:
      cadence: { type: fixed_interval, minutes: 15 }
  
  Piano:
    BM:
      start_time: "11:00"  # Override start time for Piano BM only
      cadence: { type: fixed_interval, minutes: 20 }
    MM:
      # MM uses calendar default times (09:00-17:00)
      cadence: { type: fixed_interval, minutes: 20 }
  
  Cello:
    # No time overrides - uses calendar defaults
    ALL:
      cadence: { type: fixed_interval, minutes: 15 }
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(rules_content)
        rules_path = f.name
    
    yield rules_path
    
    os.unlink(rules_path)


class TestDisciplineTimeOverrides:
    """Test per-discipline start/end time overrides."""
    
    def test_discipline_level_time_override(self, discipline_time_config):
        """Discipline-level time overrides should apply to all degrees."""
        rules = RulesEngine(discipline_time_config)
        
        # Violin should use 10:00-18:00 instead of calendar default 09:00-17:00
        slots = rules.generate_slots('Violin', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        # Check first slot starts at 10:00
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 10, f"First slot should start at 10:00, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        # Check last slot ends at or before 18:00
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 18, f"Last slot should end at or before 18:00, got {last_slot_end.hour}:{last_slot_end.minute:02d}"
    
    def test_degree_specific_time_override(self, discipline_time_config):
        """Degree-specific time overrides should apply only to that degree."""
        rules = RulesEngine(discipline_time_config)
        
        # Piano BM should use 11:00 start (calendar end time 17:00)
        slots_bm = rules.generate_slots('Piano', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots_bm) > 0, "Should generate slots"
        
        first_slot_start = slots_bm[0][0]
        assert first_slot_start.hour == 11, f"Piano BM first slot should start at 11:00, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        # Piano MM should use calendar default 09:00 start
        slots_mm = rules.generate_slots('Piano', 'MM', '2025-03-01', applicant_count=100)
        
        assert len(slots_mm) > 0, "Should generate slots"
        
        first_slot_start_mm = slots_mm[0][0]
        assert first_slot_start_mm.hour == 9, f"Piano MM first slot should start at 09:00 (calendar default), got {first_slot_start_mm.hour}:{first_slot_start_mm.minute:02d}"
        assert first_slot_start_mm.minute == 0
    
    def test_calendar_default_times(self, discipline_time_config):
        """Disciplines without overrides should use calendar default times."""
        rules = RulesEngine(discipline_time_config)
        
        # Cello has no time overrides, should use calendar default 09:00-17:00
        slots = rules.generate_slots('Cello', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 9, f"Cello should use calendar default 09:00 start, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 17, f"Cello should use calendar default 17:00 end, got {last_slot_end.hour}:{last_slot_end.minute:02d}"
    
    def test_partial_time_override(self, discipline_time_config):
        """Partial overrides (only start or only end) should work."""
        rules = RulesEngine(discipline_time_config)
        
        # Piano BM has only start_time override, should use calendar end_time (17:00)
        slots = rules.generate_slots('Piano', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        # Start should be overridden
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 11
        
        # End should use calendar default
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 17



