"""
Tests for global calendar default start/end times.
"""

from datetime import datetime, time
import pytest
import tempfile
import os

from audish.rules import RulesEngine


@pytest.fixture
def global_calendar_time_config():
    """Create temporary config file with global calendar time defaults."""
    
    rules_content = """
timezone: "America/New_York"
degree_precedence: ["BM", "MM"]

calendar:
  # Global defaults apply to all days and all disciplines
  default_start_time: "10:00"
  default_end_time: "18:00"
  
  days:
    # Days without start/end use global defaults
    - { date: 2025-03-01 }
    # Days with start/end override global defaults
    - { date: 2025-03-02, start: "09:00", end: "17:00" }

rules:
  Violin:
    ALL:
      cadence: { type: fixed_interval, minutes: 15 }
  
  Piano:
    # This discipline has its own override, which takes precedence
    start_time: "11:00"
    ALL:
      cadence: { type: fixed_interval, minutes: 20 }
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(rules_content)
        rules_path = f.name
    
    yield rules_path
    
    os.unlink(rules_path)


class TestGlobalCalendarTimes:
    """Test global calendar default start/end times."""
    
    def test_global_defaults_apply_to_days_without_times(self, global_calendar_time_config):
        """Global defaults should apply to days that don't specify start/end."""
        rules = RulesEngine(global_calendar_time_config)
        
        # Day 2025-03-01 has no start/end, should use global defaults (10:00-18:00)
        slots = rules.generate_slots('Violin', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 10, f"Should use global default 10:00 start, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 18, f"Should use global default 18:00 end, got {last_slot_end.hour}:{last_slot_end.minute:02d}"
    
    def test_day_specific_times_override_global_defaults(self, global_calendar_time_config):
        """Day-specific times should override global defaults."""
        rules = RulesEngine(global_calendar_time_config)
        
        # Day 2025-03-02 has explicit start/end (09:00-17:00), should override global defaults
        slots = rules.generate_slots('Violin', 'BM', '2025-03-02', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 9, f"Should use day-specific 09:00 start, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 17, f"Should use day-specific 17:00 end, got {last_slot_end.hour}:{last_slot_end.minute:02d}"
    
    def test_discipline_override_takes_precedence_over_global_defaults(self, global_calendar_time_config):
        """Discipline-specific times should override global calendar defaults."""
        rules = RulesEngine(global_calendar_time_config)
        
        # Piano has start_time: "11:00", should override global default (10:00)
        slots = rules.generate_slots('Piano', 'BM', '2025-03-01', applicant_count=100)
        
        assert len(slots) > 0, "Should generate slots"
        
        first_slot_start = slots[0][0]
        assert first_slot_start.hour == 11, f"Should use discipline override 11:00 start, got {first_slot_start.hour}:{first_slot_start.minute:02d}"
        assert first_slot_start.minute == 0
        
        # End time should use global default (18:00) since Piano doesn't override it
        last_slot_end = slots[-1][1]
        assert last_slot_end.hour <= 18, f"Should use global default 18:00 end, got {last_slot_end.hour}:{last_slot_end.minute:02d}"

