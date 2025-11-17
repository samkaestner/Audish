"""
Slot generation from rules.yaml.
Handles cadence types, breaks, and special patterns.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time, timedelta
import yaml


class RulesEngine:
    """Generates time slots based on rules.yaml configuration."""
    
    def __init__(self, rules_filepath: str):
        """
        Load rules configuration from YAML file.
        
        Args:
            rules_filepath: Path to rules.yaml
        """
        with open(rules_filepath, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.timezone = self.config.get('timezone', 'America/New_York')
        self.degree_precedence = self.config.get('degree_precedence', ['BM', 'MM', 'GD', 'AD', 'DMA'])
        self.teacher_presence_policy = self.config.get('teacher_presence_policy', 'prefer')
        self.same_school_spacing = self.config.get('same_school_spacing', True)
        self.double_major_window_hours = self.config.get('double_major_window_hours', 24)
        
        self.calendar = self.config.get('calendar', {})
        self.rules = self.config.get('rules', {})
    
    def get_calendar_days(self) -> List[Dict[str, Any]]:
        """Get list of calendar days from configuration."""
        return self.calendar.get('days', [])
    
    def get_degree_rank(self, degree: str) -> int:
        """
        Get precedence rank for a degree (lower is higher priority).
        
        Args:
            degree: Degree code (BM/MM/GD/AD/DMA)
            
        Returns:
            Rank (0-indexed, 0 is highest priority)
        """
        try:
            return self.degree_precedence.index(degree)
        except ValueError:
            return len(self.degree_precedence)  # Unknown degrees go last
    
    def get_discipline_rule(self, discipline: str, degree: str) -> Optional[Dict[str, Any]]:
        """
        Get scheduling rule for a discipline/degree combination.
        
        Args:
            discipline: Instrument/discipline name
            degree: Degree code
            
        Returns:
            Rule dict or None if not found
        """
        if discipline not in self.rules:
            return None
        
        discipline_rules = self.rules[discipline]
        
        # Try exact degree match first
        if degree in discipline_rules:
            return discipline_rules[degree]
        
        # Try "ALL" fallback
        if 'ALL' in discipline_rules:
            return discipline_rules['ALL']
        
        return None
    
    def generate_slots(
        self,
        discipline: str,
        degree: str,
        date_str: str,
        applicant_count: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Generate time slots for a discipline/degree on a specific date.
        
        Args:
            discipline: Instrument/discipline name
            degree: Degree code
            date_str: Date string (YYYY-MM-DD)
            applicant_count: Number of applicants needing slots
            
        Returns:
            List of (start_datetime, end_datetime) tuples
        """
        rule = self.get_discipline_rule(discipline, degree)
        if not rule:
            # Default rule: 15-minute intervals
            rule = {'cadence': {'type': 'fixed_interval', 'minutes': 15}}
        
        # Find calendar day
        calendar_day = None
        for day in self.get_calendar_days():
            day_date = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
            if day_date == date_str:
                calendar_day = day
                break
        
        if not calendar_day:
            return []
        
        # Parse date and times
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = self._parse_time(calendar_day['start'])
        end_time = self._parse_time(calendar_day['end'])
        
        day_start = datetime.combine(date_obj, start_time)
        day_end = datetime.combine(date_obj, end_time)
        
        # Generate base slots
        cadence = rule.get('cadence', {})
        cadence_type = cadence.get('type', 'fixed_interval')
        
        if cadence_type == 'per_hour':
            slots = self._generate_per_hour_slots(
                day_start, day_end, cadence, applicant_count
            )
        elif cadence_type == 'fixed_interval':
            slots = self._generate_fixed_interval_slots(
                day_start, day_end, cadence, applicant_count
            )
        else:
            # Unknown type, default to 15-minute intervals
            slots = self._generate_fixed_interval_slots(
                day_start, day_end, {'minutes': 15}, applicant_count
            )
        
        # Apply special patterns
        slots = self._apply_special_patterns(slots, rule, applicant_count)
        
        return slots
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        if ':' in time_str:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        else:
            return time(int(time_str), 0)
    
    def _generate_per_hour_slots(
        self,
        day_start: datetime,
        day_end: datetime,
        cadence: Dict[str, Any],
        applicant_count: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Generate slots using per_hour cadence.
        
        Args:
            day_start: Start of day
            day_end: End of day
            cadence: Cadence config with 'cap' and 'half_hour_distribution'
            applicant_count: Number of applicants
            
        Returns:
            List of (start, end) slot tuples
        """
        cap = cadence.get('cap', 5)
        distribution = cadence.get('half_hour_distribution', [3, 2])
        
        if len(distribution) != 2:
            distribution = [cap // 2 + cap % 2, cap // 2]
        
        slots = []
        current_time = day_start
        slot_count = 0
        
        while current_time < day_end and slot_count < applicant_count:
            # First half-hour
            first_half_slots = distribution[0]
            if first_half_slots > 0:
                interval = 30 / first_half_slots
                for i in range(first_half_slots):
                    if slot_count >= applicant_count:
                        break
                    slot_start = current_time + timedelta(minutes=int(i * interval))
                    slot_end = slot_start + timedelta(minutes=int(interval))
                    if slot_end <= day_end:
                        slots.append((slot_start, slot_end))
                        slot_count += 1
            
            # Second half-hour
            second_half_start = current_time + timedelta(minutes=30)
            second_half_slots = distribution[1]
            if second_half_slots > 0:
                interval = 30 / second_half_slots
                for i in range(second_half_slots):
                    if slot_count >= applicant_count:
                        break
                    slot_start = second_half_start + timedelta(minutes=int(i * interval))
                    slot_end = slot_start + timedelta(minutes=int(interval))
                    if slot_end <= day_end:
                        slots.append((slot_start, slot_end))
                        slot_count += 1
            
            # Move to next hour
            current_time += timedelta(hours=1)
        
        return slots
    
    def _generate_fixed_interval_slots(
        self,
        day_start: datetime,
        day_end: datetime,
        cadence: Dict[str, Any],
        applicant_count: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Generate slots using fixed_interval cadence.
        
        Args:
            day_start: Start of day
            day_end: End of day
            cadence: Cadence config with 'minutes'
            applicant_count: Number of applicants
            
        Returns:
            List of (start, end) slot tuples
        """
        interval_minutes = cadence.get('minutes', 15)
        
        slots = []
        current_time = day_start
        slot_count = 0
        
        while current_time < day_end and slot_count < applicant_count:
            slot_end = current_time + timedelta(minutes=interval_minutes)
            if slot_end <= day_end:
                slots.append((current_time, slot_end))
                slot_count += 1
            current_time += timedelta(minutes=interval_minutes)
        
        return slots
    
    def _apply_special_patterns(
        self,
        slots: List[Tuple[datetime, datetime]],
        rule: Dict[str, Any],
        applicant_count: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Apply special patterns like breaks, open time, buffers.
        
        Args:
            slots: Base slot list
            rule: Rule config
            applicant_count: Number of applicants
            
        Returns:
            Modified slot list
        """
        # Apply open_minutes_per_hour (e.g., Oboe)
        if 'open_minutes_per_hour' in rule:
            slots = self._apply_open_minutes(slots, rule['open_minutes_per_hour'])
        
        # Apply break_every_n_applicants (e.g., French Horn)
        if 'break_every_n_applicants' in rule and 'break_minutes' in rule:
            slots = self._apply_periodic_breaks(
                slots,
                rule['break_every_n_applicants'],
                rule['break_minutes']
            )
        
        # Apply mid_schedule_break (e.g., Conducting)
        if 'mid_schedule_break_minutes' in rule:
            slots = self._apply_mid_schedule_break(
                slots,
                rule['mid_schedule_break_minutes']
            )
        
        # Apply end_of_cycle_buffer (e.g., Percussion)
        if 'end_of_cycle_buffer_minutes' in rule:
            slots = self._apply_end_buffer(
                slots,
                rule['end_of_cycle_buffer_minutes']
            )
        
        return slots
    
    def _apply_open_minutes(
        self,
        slots: List[Tuple[datetime, datetime]],
        open_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Reserve open minutes per hour (remove one slot per hour).
        
        Args:
            slots: Base slot list
            open_minutes: Minutes to reserve per hour
            
        Returns:
            Modified slot list with open time reserved
        """
        if not slots:
            return slots
        
        # Group slots by hour
        slots_by_hour = {}
        for start, end in slots:
            hour_key = start.replace(minute=0, second=0, microsecond=0)
            if hour_key not in slots_by_hour:
                slots_by_hour[hour_key] = []
            slots_by_hour[hour_key].append((start, end))
        
        # Remove one slot per hour to create open time
        filtered_slots = []
        for hour_key in sorted(slots_by_hour.keys()):
            hour_slots = slots_by_hour[hour_key]
            # Keep all but last slot in the hour
            if len(hour_slots) > 1:
                filtered_slots.extend(hour_slots[:-1])
            # If only one slot, keep it anyway
            elif hour_slots:
                filtered_slots.extend(hour_slots)
        
        return filtered_slots
    
    def _apply_periodic_breaks(
        self,
        slots: List[Tuple[datetime, datetime]],
        every_n: int,
        break_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Insert breaks after every N applicants.
        
        Args:
            slots: Base slot list
            every_n: Insert break after this many slots
            break_minutes: Break duration
            
        Returns:
            Modified slot list with breaks inserted
        """
        if not slots or every_n <= 0:
            return slots
        
        result = []
        for i, (start, end) in enumerate(slots):
            result.append((start, end))
            
            # Insert break after every_n slots (but not after the last one)
            if (i + 1) % every_n == 0 and i < len(slots) - 1:
                # Shift subsequent slots by break_minutes
                break_duration = timedelta(minutes=break_minutes)
                # Add break time to all remaining slots
                remaining = slots[i + 1:]
                for j, (s, e) in enumerate(remaining):
                    slots[i + 1 + j] = (s + break_duration, e + break_duration)
        
        return result
    
    def _apply_mid_schedule_break(
        self,
        slots: List[Tuple[datetime, datetime]],
        break_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Insert a break in the middle of the schedule.
        
        Args:
            slots: Base slot list
            break_minutes: Break duration
            
        Returns:
            Modified slot list with mid-schedule break
        """
        if not slots or len(slots) < 2:
            return slots
        
        mid_index = len(slots) // 2
        break_duration = timedelta(minutes=break_minutes)
        
        # Shift second half by break duration
        result = []
        for i, (start, end) in enumerate(slots):
            if i < mid_index:
                result.append((start, end))
            else:
                result.append((start + break_duration, end + break_duration))
        
        return result
    
    def _apply_end_buffer(
        self,
        slots: List[Tuple[datetime, datetime]],
        buffer_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Reserve buffer time at end of schedule (remove last N minutes of slots).
        
        Args:
            slots: Base slot list
            buffer_minutes: Buffer duration
            
        Returns:
            Modified slot list with end buffer reserved
        """
        if not slots:
            return slots
        
        # Find last slot end time
        last_end = max(end for _, end in slots)
        cutoff_time = last_end - timedelta(minutes=buffer_minutes)
        
        # Keep only slots that end before cutoff
        return [(start, end) for start, end in slots if end <= cutoff_time]




