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
        
        # Load break configuration
        breaks_config = self.config.get('breaks', {})
        self.lunch_break = breaks_config.get('lunch', {})
        self.periodic_break = breaks_config.get('periodic', {})
    
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
    ) -> Tuple[List[Tuple[datetime, datetime]], List[Dict[str, Any]]]:
        """
        Generate time slots for a discipline/degree on a specific date.
        
        Args:
            discipline: Instrument/discipline name
            degree: Degree code
            date_str: Date string (YYYY-MM-DD)
            applicant_count: Number of applicants needing slots
            
        Returns:
            Tuple of (list of (start_datetime, end_datetime) tuples, list of break info dicts)
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
        
        # Check for discipline-specific start/end times, fall back to calendar defaults
        # Priority: degree-specific rule > ALL rule > discipline-level > calendar day > global calendar defaults
        start_time_str = None
        end_time_str = None
        
        discipline_rule = self.rules.get(discipline, {})
        if isinstance(discipline_rule, dict):
            # Check degree-specific rule first (e.g., BM, MM)
            if degree in discipline_rule and isinstance(discipline_rule[degree], dict):
                degree_rule = discipline_rule[degree]
                if 'start_time' in degree_rule:
                    start_time_str = degree_rule['start_time']
                if 'end_time' in degree_rule:
                    end_time_str = degree_rule['end_time']
            
            # Check ALL rule if not found in degree-specific
            if not start_time_str or not end_time_str:
                if 'ALL' in discipline_rule and isinstance(discipline_rule['ALL'], dict):
                    all_rule = discipline_rule['ALL']
                    if 'start_time' in all_rule and not start_time_str:
                        start_time_str = all_rule['start_time']
                    if 'end_time' in all_rule and not end_time_str:
                        end_time_str = all_rule['end_time']
            
            # Check discipline-level (top-level keys in discipline_rule)
            if 'start_time' in discipline_rule and not start_time_str:
                start_time_str = discipline_rule['start_time']
            if 'end_time' in discipline_rule and not end_time_str:
                end_time_str = discipline_rule['end_time']
        
        # Determine calendar defaults (day-specific or global)
        # Check for global calendar defaults first
        global_start_time_str = self.calendar.get('default_start_time')
        global_end_time_str = self.calendar.get('default_end_time')
        
        # Use day-specific times if available, otherwise use global defaults
        day_start_time_str = calendar_day.get('start')
        day_end_time_str = calendar_day.get('end')
        
        # Fall back through: discipline override > day-specific > global default
        if not start_time_str:
            start_time_str = day_start_time_str if day_start_time_str else global_start_time_str
        if not end_time_str:
            end_time_str = day_end_time_str if day_end_time_str else global_end_time_str
        
        # Parse times (with final fallback to 9:00/17:00 if nothing specified)
        start_time = self._parse_time(start_time_str) if start_time_str else time(9, 0)
        end_time = self._parse_time(end_time_str) if end_time_str else time(17, 0)
        
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
        
        # Apply global breaks (lunch and periodic) before discipline-specific patterns
        slots, breaks_info = self._apply_global_breaks(slots, day_start, day_end, cadence)
        
        # Apply special patterns
        slots = self._apply_special_patterns(slots, rule, applicant_count)
        
        return slots, breaks_info
    
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
    
    def _apply_global_breaks(
        self,
        slots: List[Tuple[datetime, datetime]],
        day_start: datetime,
        day_end: datetime,
        cadence: Dict[str, Any]
    ) -> Tuple[List[Tuple[datetime, datetime]], List[Dict[str, Any]]]:
        """
        Apply global breaks: lunch break and periodic breaks.
        
        Args:
            slots: Base slot list
            day_start: Start of day
            day_end: End of day
            cadence: Cadence config to determine slot duration
            
        Returns:
            Tuple of (modified slot list, list of break info dicts)
            Break info dicts have: {'type': 'lunch'|'periodic', 'start': datetime, 'end': datetime}
        """
        breaks_info = []
        
        if not slots:
            return slots, breaks_info
        
        # Calculate schedule duration in hours
        schedule_duration_hours = (day_end - day_start).total_seconds() / 3600
        
        # Determine slot duration from cadence
        slot_duration_minutes = self._get_slot_duration_minutes(cadence)
        
        # Apply lunch break if enabled and schedule is long enough
        if (self.lunch_break.get('enabled', False) and 
            schedule_duration_hours > self.lunch_break.get('min_schedule_hours', 4)):
            slots, lunch_break_info = self._apply_lunch_break(slots, day_start, slot_duration_minutes)
            if lunch_break_info:
                breaks_info.append(lunch_break_info)
        
        # Apply periodic breaks if enabled
        if self.periodic_break.get('enabled', False):
            slots, periodic_breaks_info = self._apply_periodic_breaks_global(slots, day_start, cadence)
            breaks_info.extend(periodic_breaks_info)
        
        return slots, breaks_info
    
    def _get_slot_duration_minutes(self, cadence: Dict[str, Any]) -> int:
        """
        Get slot duration in minutes from cadence config.
        
        Args:
            cadence: Cadence config
            
        Returns:
            Slot duration in minutes
        """
        cadence_type = cadence.get('type', 'fixed_interval')
        
        if cadence_type == 'fixed_interval':
            return cadence.get('minutes', 15)
        elif cadence_type == 'per_hour':
            # For per_hour, calculate average slot duration
            cap = cadence.get('cap', 5)
            distribution = cadence.get('half_hour_distribution', [3, 2])
            if len(distribution) == 2 and sum(distribution) > 0:
                # Average slot duration = 60 minutes / total slots per hour
                return int(60 / sum(distribution))
            else:
                return int(60 / cap) if cap > 0 else 15
        
        return 15  # Default
    
    def _apply_lunch_break(
        self,
        slots: List[Tuple[datetime, datetime]],
        day_start: datetime,
        slot_duration_minutes: int
    ) -> Tuple[List[Tuple[datetime, datetime]], Optional[Dict[str, Any]]]:
        """
        Apply lunch break (1-2pm) by removing overlapping slots.
        
        Args:
            slots: Slot list
            day_start: Start of day (to determine date)
            slot_duration_minutes: Duration of one slot in minutes
            
        Returns:
            Tuple of (modified slot list, break info dict or None)
        """
        lunch_start_str = self.lunch_break.get('start', '13:00')
        lunch_end_str = self.lunch_break.get('end', '14:00')
        
        lunch_start_time = self._parse_time(lunch_start_str)
        lunch_end_time = self._parse_time(lunch_end_str)
        
        lunch_start = datetime.combine(day_start.date(), lunch_start_time)
        lunch_end = datetime.combine(day_start.date(), lunch_end_time)
        
        lunch_duration = lunch_end - lunch_start
        lunch_duration_minutes = int(lunch_duration.total_seconds() / 60)
        
        result = []
        break_applied = False
        
        for start, end in slots:
            # Check if slot overlaps with lunch break
            if not (end <= lunch_start or start >= lunch_end):
                # Slot overlaps with lunch, skip it (remove it)
                break_applied = True
                continue
            
            # Keep slot as-is (don't shift - just remove overlapping slots)
            # This creates a natural gap during lunch time
            result.append((start, end))
        
        # Return break info if lunch break was applied
        break_info = None
        if break_applied:
            break_info = {
                'type': 'lunch',
                'start': lunch_start,
                'end': lunch_end
            }
        
        return result, break_info
    
    def _apply_periodic_breaks_global(
        self,
        slots: List[Tuple[datetime, datetime]],
        day_start: datetime,
        cadence: Dict[str, Any]
    ) -> Tuple[List[Tuple[datetime, datetime]], List[Dict[str, Any]]]:
        """
        Apply periodic breaks every N hours (break duration = one slot).
        
        Args:
            slots: Slot list (may already have lunch break applied)
            day_start: Start of day
            cadence: Cadence config to determine slot duration
            
        Returns:
            Tuple of (modified slot list, list of break info dicts)
        """
        if not slots:
            return slots
        
        interval_hours = self.periodic_break.get('interval_hours', 2)
        duration_slots = self.periodic_break.get('duration_slots', 1)
        
        # Get slot duration
        slot_duration_minutes = self._get_slot_duration_minutes(cadence)
        break_duration = timedelta(minutes=slot_duration_minutes * duration_slots)
        
        # Calculate break times (every N hours from original day start)
        # Note: lunch break no longer shifts slots, it just removes overlapping slots
        break_times = []
        current_break_time = day_start + timedelta(hours=interval_hours)
        
        # Check if lunch break is enabled (to skip overlapping breaks)
        lunch_start = None
        lunch_end = None
        if self.lunch_break.get('enabled', False):
            lunch_start_time = self._parse_time(self.lunch_break.get('start', '13:00'))
            lunch_end_time = self._parse_time(self.lunch_break.get('end', '14:00'))
            lunch_start = datetime.combine(day_start.date(), lunch_start_time)
            lunch_end = datetime.combine(day_start.date(), lunch_end_time)
        
        # Find last slot end time to know when to stop
        last_slot_end = max(end for _, end in slots)
        
        while current_break_time < last_slot_end:
            # Skip break times that overlap with lunch break
            if lunch_start and lunch_end:
                break_end_time = current_break_time + break_duration
                # If periodic break overlaps with lunch break, skip it
                if not (break_end_time <= lunch_start or current_break_time >= lunch_end):
                    current_break_time += timedelta(hours=interval_hours)
                    continue
                
                # Also skip periodic breaks that occur too soon after lunch ends
                # (within 1 hour of lunch end) to avoid creating excessively long gaps
                # This prevents a periodic break from immediately following lunch break
                time_after_lunch = (current_break_time - lunch_end).total_seconds() / 3600
                if 0 <= time_after_lunch < 1.0:  # Within 1 hour after lunch end
                    # Skip this break to avoid long gap after lunch
                    current_break_time += timedelta(hours=interval_hours)
                    continue
            
            break_times.append(current_break_time)
            current_break_time += timedelta(hours=interval_hours)
        
        if not break_times:
            return slots, []
        
        # Build break info list
        breaks_info = []
        for break_time in break_times:
            break_end = break_time + break_duration
            breaks_info.append({
                'type': 'periodic',
                'start': break_time,
                'end': break_end
            })
        
        # Apply breaks: remove slots that overlap with break times, shift subsequent slots
        result = []
        cumulative_shift = timedelta(0)
        break_idx = 0
        
        for start, end in slots:
            # Apply cumulative shift from previous breaks
            adjusted_start = start + cumulative_shift
            adjusted_end = end + cumulative_shift
            
            # Process all breaks that affect this slot
            while break_idx < len(break_times):
                break_time = break_times[break_idx]
                break_end = break_time + break_duration
                
                # If slot ends before this break starts, we're done
                if adjusted_end <= break_time:
                    break
                
                # If slot overlaps with this break, skip the slot
                if not (adjusted_end <= break_time or adjusted_start >= break_end):
                    # Slot overlaps with break, skip it entirely
                    break_idx += 1
                    # Don't add this slot to result
                    adjusted_start = None
                    adjusted_end = None
                    break
                
                # If slot starts after this break ends, shift it and move to next break
                if adjusted_start >= break_end:
                    cumulative_shift += break_duration
                    break_idx += 1
                    # Recalculate adjusted times
                    adjusted_start = start + cumulative_shift
                    adjusted_end = end + cumulative_shift
                else:
                    break
            
            # Add slot if it wasn't skipped
            if adjusted_start is not None and adjusted_end is not None:
                result.append((adjusted_start, adjusted_end))
        
        return result, breaks_info
    
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





