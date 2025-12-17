"""
Core scheduling algorithm.
Implements greedy assignment with constraints, conflict tracking, and numbering.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta, date
from collections import defaultdict
import copy

from . import reason_codes
from .faculty import is_faculty_available
from .faculty_names import match_teacher_name
from .rules import RulesEngine


class Scheduler:
    """Main scheduling engine."""
    
    def __init__(
        self,
        rules_engine: RulesEngine,
        faculty_availability: Dict[str, Dict[str, List[Tuple[Any, Any]]]],
        applicants: List[Dict[str, Any]],
        mapper: Any,
        faculty_name_map: Dict[str, str]
    ):
        """
        Initialize scheduler.
        
        Args:
            rules_engine: RulesEngine instance
            faculty_availability: Faculty availability map from faculty.py
            applicants: List of normalized applicant dicts
            mapper: ColumnMapper instance for denormalization
            faculty_name_map: Normalized name to faculty name mapping
        """
        self.rules = rules_engine
        self.faculty_availability = faculty_availability
        self.applicants = applicants
        self.mapper = mapper
        self.faculty_name_map = faculty_name_map
        
        # Check if registration date field is configured in mapping
        self.registration_date_field = self._check_registration_date_field()
        
        # Scheduling state
        self.scheduled: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []
        self.breaks: List[Dict[str, Any]] = []  # Break information for output
        self.slot_assignments: Dict[Tuple[str, str, datetime], str] = {}  # (discipline, date, time) -> applicant_id
        self.applicant_slots: Dict[str, List[Tuple[datetime, datetime]]] = {}  # applicant_id -> [(start, end), ...]
    
    def schedule(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Run the scheduling algorithm.
        
        Returns:
            Tuple of (scheduled_applicants, conflicts)
        """
        # Group applicants by discipline
        by_discipline = defaultdict(list)
        for applicant in self.applicants:
            discipline = applicant.get('major') or applicant.get('department')
            if discipline:
                by_discipline[discipline].append(applicant)
        
        # Process each discipline
        for discipline, discipline_applicants in by_discipline.items():
            self._schedule_discipline(discipline, discipline_applicants)
        
        # Number auditions per discipline across all days
        self._number_auditions()
        
        # Validate registration dates and flag conflicts
        self._validate_registration_dates()
        
        return self.scheduled, self.conflicts
    
    def _schedule_discipline(self, discipline: str, applicants: List[Dict[str, Any]]) -> None:
        """
        Schedule all applicants for a single discipline.
        
        Implements per-day degree ordering preference: within each audition day,
        BMs are scheduled early, MM/GDs in the middle, AD/DMAs at the end.
        
        Args:
            discipline: Discipline/instrument name
            applicants: List of applicants in this discipline
        """
        # Precompute valid slots for each applicant
        applicant_slots = []
        for applicant in applicants:
            valid_slots = self._compute_valid_slots(applicant, discipline)
            applicant_slots.append({
                'applicant': applicant,
                'valid_slots': valid_slots,
                'num_valid': len(valid_slots)
            })
        
        # Order applicants by: degree precedence → Juilliard students first → fewest valid slots → stable ID
        # This ensures current Juilliard students are grouped together within each degree
        def is_current_juilliard(applicant: Dict[str, Any]) -> int:
            """Return 0 for Juilliard students (first), 1 for external (second)."""
            juilliard_status = applicant.get('juilliard_status', '')
            if juilliard_status and 'juilliard' in str(juilliard_status).lower():
                return 0  # Juilliard students scheduled first
            return 1  # External students scheduled after
        
        applicant_slots.sort(key=lambda x: (
            self.rules.get_degree_rank(x['applicant'].get('degree', '')),
            is_current_juilliard(x['applicant']),
            x['num_valid'],
            x['applicant'].get('id', '')
        ))
        
        # Track per-day slot usage by degree to enforce within-day ordering
        # Key: (date_str, degree_rank) -> latest end time for that degree on that day
        per_day_degree_end_times: Dict[Tuple[str, int], datetime] = {}
        
        # Greedy assignment with per-day degree ordering preference
        for item in applicant_slots:
            applicant = item['applicant']
            valid_slots = item['valid_slots']
            degree_rank = self.rules.get_degree_rank(applicant.get('degree', ''))
            
            # Early conflict detection: check for missing required data before attempting to schedule
            # This prevents defaulting to the first calendar day when data is incomplete
            
            # Check for missing registration date
            if self.registration_date_field:
                registration_date_str = self._parse_registration_date(applicant)
                if registration_date_str is None:
                    self._add_conflict(
                        applicant,
                        reason_codes.REGISTRATION_DATE_MISSING,
                        "Registration date is missing from applicant data - cannot schedule"
                    )
                    continue
                
                # Check if registration date is in the calendar
                calendar_dates = set()
                for day in self.rules.get_calendar_days():
                    day_date = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
                    calendar_dates.add(day_date)
                
                if registration_date_str not in calendar_dates:
                    self._add_conflict(
                        applicant,
                        reason_codes.REGISTRATION_DATE_NOT_IN_CALENDAR,
                        f"Registration date {registration_date_str} is not an audition day. "
                        f"Calendar days: {', '.join(sorted(calendar_dates))}"
                    )
                    continue
            
            # Check for missing faculty availability for teachers with preferences
            teacher1 = applicant.get('teacher1')
            teacher2 = applicant.get('teacher2')
            teacher3 = applicant.get('teacher3')
            has_teacher_preferences = bool(teacher1 or teacher2 or teacher3)
            
            if has_teacher_preferences:
                # Check if any preferred teacher has availability data
                has_faculty_data = False
                teacher_list = []
                teacher_availability_info = []
                
                for teacher_name in [teacher1, teacher2, teacher3]:
                    if teacher_name:
                        teacher_list.append(teacher_name)
                        from .faculty_names import match_teacher_name
                        faculty_name = match_teacher_name(teacher_name, self.faculty_name_map)
                        if faculty_name and faculty_name in self.faculty_availability:
                            # Check if this faculty has any availability on any day
                            available_days = []
                            for date_str, date_avail in self.faculty_availability[faculty_name].items():
                                if date_avail:  # Non-empty list of time ranges
                                    has_faculty_data = True
                                    available_days.append(date_str)
                            
                            if available_days:
                                teacher_availability_info.append(f"{teacher_name} available on: {', '.join(sorted(available_days))}")
                        if has_faculty_data:
                            break
                
                if not has_faculty_data:
                    # Get registration date for better diagnostics
                    registration_date_str = None
                    if self.registration_date_field:
                        registration_date_str = self._parse_registration_date(applicant)
                    
                    details = f"None of the preferred teachers ({', '.join(teacher_list)}) have availability data in the faculty availability file"
                    if registration_date_str:
                        details += f". Applicant registration date: {registration_date_str}"
                    
                    self._add_conflict(
                        applicant,
                        reason_codes.TEACHER_UNAVAILABLE,
                        details
                    )
                    continue
            
            # Apply per-day degree ordering: filter slots to respect within-day ordering
            # For each day, prefer slots that don't conflict with the ordering preference
            filtered_slots = self._apply_per_day_degree_filter(
                valid_slots, degree_rank, per_day_degree_end_times
            )
            
            # If filtering removed all slots, fall back to original valid_slots
            # (degree ordering is a preference, not a hard constraint)
            if not filtered_slots and valid_slots:
                filtered_slots = valid_slots
            
            assigned = False
            for slot_info in filtered_slots:
                if self._try_assign_slot(applicant, discipline, slot_info):
                    assigned = True
                    
                    # Update per-day degree end time tracking
                    date_str = slot_info['date']
                    slot_end = slot_info['end']
                    key = (date_str, degree_rank)
                    if key not in per_day_degree_end_times or slot_end > per_day_degree_end_times[key]:
                        per_day_degree_end_times[key] = slot_end
                        
                    break
            
            if not assigned:
                # Determine conflict reason
                # Note: Missing registration date and faculty availability are caught earlier,
                # so this section handles other conflict types (capacity, scheduling conflicts, etc.)
                teacher1 = applicant.get('teacher1')
                teacher2 = applicant.get('teacher2')
                teacher3 = applicant.get('teacher3')
                has_teacher_preferences = bool(teacher1 or teacher2 or teacher3)
                degree = applicant.get('degree', 'MM')
                
                if not valid_slots:
                    # Check if it's because no teachers are available
                    if has_teacher_preferences:
                        # Check if any day has teacher availability
                        # Check multiple slots throughout each day (not just first slot)
                        has_any_teacher_availability = False
                        teacher_available_days = []
                        
                        # Get registration date if applicable
                        registration_date_str = None
                        if self.registration_date_field:
                            registration_date_str = self._parse_registration_date(applicant)
                        
                        for day in self.rules.get_calendar_days():
                            date_str = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
                            
                            # Generate slots to check teacher availability throughout the day
                            sample_slots, _ = self.rules.generate_slots(discipline, degree, date_str, applicant_count=100)
                            
                            # Check multiple slots throughout the day (not just first)
                            day_has_teacher = False
                            for slot_start, _ in sample_slots[:10]:  # Check first 10 slots to sample throughout day
                                teacher_rank = self._check_teacher_presence(
                                    teacher1, teacher2, teacher3, date_str, slot_start
                                )
                                if teacher_rank > 0:
                                    day_has_teacher = True
                                    has_any_teacher_availability = True
                                    break
                            
                            if day_has_teacher:
                                teacher_available_days.append(date_str)
                        
                        if not has_any_teacher_availability:
                            reason = reason_codes.TEACHER_UNAVAILABLE
                            teacher_list = [t for t in [teacher1, teacher2, teacher3] if t]
                            details = f"None of the preferred teachers ({', '.join(teacher_list)}) are available on any scheduled day"
                        else:
                            # Teacher is available on some days, but applicant couldn't be scheduled
                            reason = reason_codes.NO_VALID_SLOTS
                            teacher_list = [t for t in [teacher1, teacher2, teacher3] if t]
                            details = f"No available slots matching all constraints. "
                            details += f"Preferred teachers: {', '.join(teacher_list)}. "
                            details += f"Teacher available on days: {', '.join(teacher_available_days)}. "
                            if registration_date_str:
                                details += f"Applicant registration date: {registration_date_str}. "
                            if registration_date_str and registration_date_str not in teacher_available_days:
                                details += "NOTE: Teacher not available on applicant's registration date."
                    else:
                        reason = reason_codes.NO_VALID_SLOTS
                        details = "No available slots matching all constraints"
                else:
                    reason = reason_codes.CAPACITY_EXCEEDED
                    details = "All available slots at capacity"
                
                self._add_conflict(applicant, reason, details)
    
    def _apply_per_day_degree_filter(
        self,
        valid_slots: List[Dict[str, Any]],
        degree_rank: int,
        per_day_degree_end_times: Dict[Tuple[str, int], datetime]
    ) -> List[Dict[str, Any]]:
        """
        Filter and re-order slots to enforce per-day degree ordering preference.
        
        Within each day, applicants should be scheduled in degree order:
        BMs first (morning), MM/GDs middle, AD/DMAs at end.
        
        Args:
            valid_slots: List of valid slot info dicts
            degree_rank: Rank of the applicant's degree (0=BM, higher=lower priority)
            per_day_degree_end_times: Tracking dict of (date, degree_rank) -> latest end time
            
        Returns:
            Filtered list of slots respecting per-day degree ordering
        """
        if not valid_slots:
            return valid_slots
        
        filtered = []
        for slot in valid_slots:
            date_str = slot['date']
            slot_start = slot['start']
            
            # Check if any higher-priority degree has been scheduled on this day
            # If so, this slot should start after their latest slot ends
            should_include = True
            for prev_rank in range(degree_rank):
                key = (date_str, prev_rank)
                if key in per_day_degree_end_times:
                    # Higher priority degree was scheduled on this day
                    # Prefer slots that start at or after their end time
                    if slot_start < per_day_degree_end_times[key]:
                        should_include = False
                        break
            
            if should_include:
                filtered.append(slot)
        
        return filtered
    
    def _compute_valid_slots(
        self,
        applicant: Dict[str, Any],
        discipline: str
    ) -> List[Dict[str, Any]]:
        """
        Compute valid slots for an applicant, ranked by preference.
        
        Args:
            applicant: Normalized applicant dict
            discipline: Discipline name
            
        Returns:
            List of slot info dicts, sorted by preference (best first)
        """
        degree = applicant.get('degree', 'MM')
        applicant_id = applicant.get('id', '')
        
        # Get teacher preferences
        teacher1 = applicant.get('teacher1')
        teacher2 = applicant.get('teacher2')
        teacher3 = applicant.get('teacher3')
        
        # Check if applicant has any teacher preferences
        has_teacher_preferences = bool(teacher1 or teacher2 or teacher3)
        
        # Get registration date if present and configured
        registration_date_str = None
        if self.registration_date_field:
            registration_date_str = self._parse_registration_date(applicant)
            # If registration date field is configured but missing for this applicant,
            # return empty slots list to force a conflict instead of defaulting to first day
            if registration_date_str is None:
                return []
        
        # If applicant has teacher preferences, check if any of those teachers exist in faculty availability
        if has_teacher_preferences:
            has_any_faculty_data = False
            teacher_available_on_registration_date = False
            
            for teacher_name in [teacher1, teacher2, teacher3]:
                if teacher_name:
                    # Match teacher name to faculty name
                    from .faculty_names import match_teacher_name
                    faculty_name = match_teacher_name(teacher_name, self.faculty_name_map)
                    if faculty_name and faculty_name in self.faculty_availability:
                        # Check if this faculty member has any availability on any day
                        for date_str, date_avail in self.faculty_availability[faculty_name].items():
                            if date_avail:  # Non-empty list of time ranges
                                has_any_faculty_data = True
                                # Check if teacher available on registration date (if applicable)
                                if registration_date_str and date_str == registration_date_str:
                                    teacher_available_on_registration_date = True
                                break
                    if has_any_faculty_data:
                        break
            
            # If applicant has teacher preferences but none of those teachers have any availability data,
            # return empty slots to force a conflict
            if not has_any_faculty_data:
                return []
            
            # If registration date is set but no teacher is available on that date,
            # we'll still generate slots (they'll all be filtered out later with proper reason)
            # This allows for better error messaging
        
        valid_slots = []
        
        # Generate slots for each calendar day
        for day in self.rules.get_calendar_days():
            date_str = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
            
            # If applicant has a registration date, only consider slots on that date
            if registration_date_str and date_str != registration_date_str:
                continue
            
            # Generate slots for this discipline/degree/day
            slots, breaks_info = self.rules.generate_slots(discipline, degree, date_str, applicant_count=100)
            
            # Store break information for this discipline/date (only once per discipline/date)
            # Check if we've already stored breaks for this discipline/date combo
            break_key = (discipline, date_str)
            if not hasattr(self, '_break_keys_stored'):
                self._break_keys_stored = set()
            
            if break_key not in self._break_keys_stored:
                for break_info in breaks_info:
                    break_info['discipline'] = discipline
                    break_info['date'] = date_str
                    self.breaks.append(break_info)
                self._break_keys_stored.add(break_key)
            
            for start_time, end_time in slots:
                # Check teacher presence
                teacher_rank = self._check_teacher_presence(
                    teacher1, teacher2, teacher3, date_str, start_time
                )
                
                # Apply teacher presence policy
                # If applicant has teacher preferences, they should only be scheduled
                # on days when at least one preferred teacher is available
                if has_teacher_preferences and teacher_rank == 0:
                    continue  # No preferred teacher available, skip slot
                
                # For "require" policy, also filter if no teacher (redundant with above when has preferences)
                if self.rules.teacher_presence_policy == 'require' and teacher_rank == 0:
                    continue  # No preferred teacher available, skip slot
                
                # Check if applicant already has a slot (for double majors)
                if self._conflicts_with_existing_slot(applicant_id, start_time, end_time):
                    continue
                
                # Slot is valid, add to list with ranking info
                valid_slots.append({
                    'date': date_str,
                    'start': start_time,
                    'end': end_time,
                    'teacher_rank': teacher_rank,
                })
        
        # Sort by: teacher rank (desc) → earliest time
        # The per-day degree filter handles ordering BM → MM/GD → AD/DMA within each day
        valid_slots.sort(key=lambda x: (-x['teacher_rank'], x['start']))
        
        return valid_slots
    
    def _check_teacher_presence(
        self,
        teacher1: Optional[str],
        teacher2: Optional[str],
        teacher3: Optional[str],
        date_str: str,
        slot_start: datetime
    ) -> int:
        """
        Check which teacher choice is available for a slot.
        
        Args:
            teacher1, teacher2, teacher3: Teacher preferences
            date_str: Date string (YYYY-MM-DD)
            slot_start: Slot start datetime
            
        Returns:
            Teacher rank: 3 for 1st choice, 2 for 2nd, 1 for 3rd, 0 for none
        """
        teachers = [
            (teacher1, 3),
            (teacher2, 2),
            (teacher3, 1)
        ]
        
        for teacher, rank in teachers:
            if not teacher:
                continue
            
            # Match teacher name to faculty name
            faculty_name = match_teacher_name(teacher, self.faculty_name_map)
            
            if faculty_name and is_faculty_available(
                faculty_name, date_str, slot_start, self.faculty_availability
            ):
                return rank
        
        return 0
    
    def _conflicts_with_existing_slot(
        self,
        applicant_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if a slot conflicts with applicant's existing audition(s).
        
        Args:
            applicant_id: Applicant ID
            start_time: Proposed slot start
            end_time: Proposed slot end
            
        Returns:
            True if conflict exists
        """
        if applicant_id not in self.applicant_slots:
            return False
        
        for existing_start, existing_end in self.applicant_slots[applicant_id]:
            # Check for overlap
            if not (end_time <= existing_start or start_time >= existing_end):
                return True
            
            # Check 24-hour window constraint for double majors
            time_diff = abs((start_time - existing_start).total_seconds() / 3600)
            if time_diff > self.rules.double_major_window_hours:
                return True
        
        return False
    
    def _try_assign_slot(
        self,
        applicant: Dict[str, Any],
        discipline: str,
        slot_info: Dict[str, Any]
    ) -> bool:
        """
        Try to assign an applicant to a slot.
        
        Args:
            applicant: Applicant dict
            discipline: Discipline name
            slot_info: Slot info dict with date, start, end, teacher_rank
            
        Returns:
            True if assignment successful, False otherwise
        """
        date_str = slot_info['date']
        start_time = slot_info['start']
        end_time = slot_info['end']
        applicant_id = applicant.get('id', '')
        
        # Check if slot is already taken
        slot_key = (discipline, date_str, start_time)
        if slot_key in self.slot_assignments:
            return False
        
        # Validate teacher availability: if applicant has teacher preferences,
        # ensure at least one preferred teacher is available for this slot
        teacher1 = applicant.get('teacher1')
        teacher2 = applicant.get('teacher2')
        teacher3 = applicant.get('teacher3')
        has_teacher_preferences = bool(teacher1 or teacher2 or teacher3)
        
        if has_teacher_preferences:
            # Re-check teacher presence for this specific slot as a safety validation
            teacher_rank = self._check_teacher_presence(
                teacher1, teacher2, teacher3, date_str, start_time
            )
            if teacher_rank == 0:
                # This should not happen if _compute_valid_slots worked correctly,
                # but we validate here as a safety check
                return False
        
        # Check same-school spacing if enabled
        if self.rules.same_school_spacing:
            if not self._check_same_school_spacing(applicant, discipline, date_str, start_time):
                return False
        
        # Assign slot
        self.slot_assignments[slot_key] = applicant_id
        
        if applicant_id not in self.applicant_slots:
            self.applicant_slots[applicant_id] = []
        self.applicant_slots[applicant_id].append((start_time, end_time))
        
        # Add to scheduled list
        scheduled_record = copy.deepcopy(applicant)
        scheduled_record['Music Audition Date'] = date_str
        # Format time as 12-hour with AM/PM (e.g., "9:00 AM", "2:30 PM")
        # %I produces 01-12, so remove leading zero from hour for single-digit hours
        time_str = start_time.strftime('%I:%M %p').lstrip('0')
        scheduled_record['Music Audition Time'] = time_str
        scheduled_record['_discipline'] = discipline
        scheduled_record['_teacher_rank'] = slot_info['teacher_rank']
        self.scheduled.append(scheduled_record)
        
        return True
    
    def _check_same_school_spacing(
        self,
        applicant: Dict[str, Any],
        discipline: str,
        date_str: str,
        slot_start: datetime
    ) -> bool:
        """
        Check if assigning this slot would violate same-school spacing.
        
        Args:
            applicant: Applicant dict
            discipline: Discipline name
            date_str: Date string
            slot_start: Slot start time
            
        Returns:
            True if spacing is acceptable
        """
        school_org = applicant.get('school_org')
        if not school_org:
            return True
        
        # Current Juilliard students are exempt
        juilliard_status = applicant.get('juilliard_status', '')
        if juilliard_status and 'juilliard' in str(juilliard_status).lower():
            return True
        
        # Check adjacent slots (previous and next)
        for scheduled in self.scheduled:
            # Only check same discipline and date
            if scheduled.get('_discipline') != discipline:
                continue
            if scheduled.get('Music Audition Date') != date_str:
                continue
            
            # Parse scheduled time
            scheduled_time_str = scheduled.get('Music Audition Time', '')
            if not scheduled_time_str:
                continue
            
            try:
                # Parse time string (supports both 24-hour "HH:MM" and 12-hour "H:MM AM/PM")
                from .faculty import parse_time
                time_obj = parse_time(scheduled_time_str)
                if time_obj:
                    scheduled_datetime = slot_start.replace(hour=time_obj.hour, minute=time_obj.minute)
                else:
                    continue
            except (ValueError, AttributeError):
                continue
            
            # Check if adjacent (within 30 minutes)
            time_diff_minutes = abs((slot_start - scheduled_datetime).total_seconds() / 60)
            if time_diff_minutes < 30:
                # Check if same school
                scheduled_school = scheduled.get('school_org')
                if scheduled_school == school_org:
                    return False  # Same school, too close
        
        return True
    
    def _add_conflict(
        self,
        applicant: Dict[str, Any],
        reason_code: str,
        details: str
    ) -> None:
        """
        Add an applicant to the conflicts list.
        
        Preserves all identifying fields from the original input to make it
        easier to understand why someone was excluded.
        
        Args:
            applicant: Applicant dict
            reason_code: Reason code constant
            details: Human-readable details
        """
        # Start with all original data from the input file
        conflict_record = {}
        if '_original' in applicant:
            conflict_record = dict(applicant['_original'])
        
        # Add/override with conflict-specific fields at the end
        # These will appear as additional columns in the output
        conflict_record['_ReasonCode'] = reason_code
        conflict_record['_ConflictDetails'] = details
        
        # Also store the discipline for grouping purposes
        conflict_record['_Discipline'] = applicant.get('major') or applicant.get('department', '')
        
        self.conflicts.append(conflict_record)
    
    def _number_auditions(self) -> None:
        """
        Assign sequential Music Audition Order per discipline across all days.
        Orders by degree precedence first (BM → MM/GD → AD → DMA), then chronologically.
        """
        from .faculty import parse_time
        
        def get_sort_key(record: Dict[str, Any]) -> Tuple[int, str, datetime]:
            """Create a sort key that sorts by degree precedence, then date/time."""
            # Get degree rank (0=BM, 1=MM, etc.)
            degree = record.get('degree', '')
            degree_rank = self.rules.get_degree_rank(degree)
            
            date_str = record.get('Music Audition Date', '')
            time_str = record.get('Music Audition Time', '')
            
            # Parse the time to get proper chronological ordering
            time_obj = parse_time(time_str) if time_str else None
            
            if date_str and time_obj:
                # Create a full datetime for proper sorting
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d').replace(
                        hour=time_obj.hour, minute=time_obj.minute
                    )
                    return (degree_rank, date_str, dt)
                except ValueError:
                    pass
            
            # Fallback: use a very late datetime to push invalid entries to the end
            return (degree_rank, date_str, datetime.max)
        
        # Group by discipline
        by_discipline = defaultdict(list)
        for scheduled in self.scheduled:
            discipline = scheduled.get('_discipline', '')
            if discipline:
                by_discipline[discipline].append(scheduled)
        
        # Number each discipline
        for discipline, records in by_discipline.items():
            # Sort by degree precedence, then date, then time
            records.sort(key=get_sort_key)
            
            # Assign sequential numbers
            for order, record in enumerate(records, start=1):
                record['Music Audition Order'] = order
    
    def _check_registration_date_field(self) -> Optional[str]:
        """
        Check if registration date field is configured in the mapping.
        
        Returns:
            Field name if configured, None otherwise
        """
        date_fields = [
            'registration_date',
            'event_date',
            'event_registration_date',
            'registered_date',
            'audition_date',
        ]
        
        for field in date_fields:
            if self.mapper.get_applicant_column(field):
                return field
        
        return None
    
    def _parse_registration_date(self, applicant: Dict[str, Any]) -> Optional[str]:
        """
        Parse registration date from applicant data.
        
        Looks for common field names like 'registration_date', 'event_date', etc.
        Supports multiple date formats.
        
        Args:
            applicant: Normalized applicant dict
            
        Returns:
            Date string in YYYY-MM-DD format, or None if not found
        """
        # Check various possible field names for registration date
        date_fields = [
            'registration_date',
            'event_date',
            'event_registration_date',
            'registered_date',
            'audition_date',
        ]
        
        for field in date_fields:
            date_value = applicant.get(field)
            if not date_value:
                continue
            
            # Try to parse various date formats
            if isinstance(date_value, datetime):
                return date_value.strftime('%Y-%m-%d')
            elif isinstance(date_value, date):
                return date_value.strftime('%Y-%m-%d')
            elif isinstance(date_value, str):
                date_value = date_value.strip()
                if not date_value:
                    continue
                
                # Try common date and datetime formats
                # Include formats with time since "Event – Most Recent Registration Event Date/Time"
                # may contain values like "3/7/2025 10:30:00 AM"
                formats = [
                    # Date only formats
                    '%Y-%m-%d',           # 2025-02-28
                    '%m/%d/%Y',           # 2/28/2025 or 02/28/2025
                    '%m-%d-%Y',           # 2-28-2025
                    '%Y/%m/%d',           # 2025/02/28
                    # Datetime formats (time will be ignored, only date extracted)
                    '%m/%d/%Y %I:%M:%S %p',  # 3/7/2025 10:30:00 AM
                    '%m/%d/%Y %I:%M %p',     # 3/7/2025 10:30 AM
                    '%m/%d/%Y %H:%M:%S',     # 3/7/2025 14:30:00
                    '%m/%d/%Y %H:%M',        # 3/7/2025 14:30
                    '%Y-%m-%d %H:%M:%S',     # 2025-03-07 14:30:00
                    '%Y-%m-%d %H:%M',        # 2025-03-07 14:30
                    '%Y-%m-%dT%H:%M:%S',     # 2025-03-07T14:30:00 (ISO format)
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        
        return None
    
    def _validate_registration_dates(self) -> None:
        """
        Validate that scheduled applicants match their registration dates.
        Move mismatched applicants to conflicts.
        """
        # Create lookup for applicants by ID
        applicant_lookup = {app.get('id'): app for app in self.applicants}
        
        # Check each scheduled applicant
        to_remove = []
        for scheduled_record in self.scheduled:
            applicant_id = scheduled_record.get('id')
            if not applicant_id:
                continue
            
            applicant = applicant_lookup.get(applicant_id)
            if not applicant:
                continue
            
            # Only validate registration dates if the field is configured
            if not self.registration_date_field:
                continue
            
            # Get registration date
            registration_date_str = self._parse_registration_date(applicant)
            scheduled_date_str = scheduled_record.get('Music Audition Date')
            
            # Check if registration date is missing
            # Note: This should have been caught before scheduling, but we check again
            # as a safety measure in case someone was scheduled despite missing registration date
            if registration_date_str is None:
                to_remove.append(scheduled_record)
                # Only add conflict if not already in conflicts (avoid duplicates)
                conflict_exists = any(
                    c.get('ApplicantID') == applicant_id and 
                    c.get('ReasonCode') == reason_codes.REGISTRATION_DATE_MISSING
                    for c in self.conflicts
                )
                if not conflict_exists:
                    self._add_conflict(
                        applicant,
                        reason_codes.REGISTRATION_DATE_MISSING,
                        "Registration date is missing from applicant data"
                    )
                continue
            
            # Check if scheduled date matches registration date
            if scheduled_date_str != registration_date_str:
                to_remove.append(scheduled_record)
                self._add_conflict(
                    applicant,
                    reason_codes.REGISTRATION_DATE_MISMATCH,
                    f"Assigned date {scheduled_date_str} does not match registration date {registration_date_str}"
                )
                # Remove from slot assignments
                discipline = scheduled_record.get('_discipline', '')
                time_str = scheduled_record.get('Music Audition Time', '')
                if discipline and scheduled_date_str and time_str:
                    try:
                        # Parse time to get datetime
                        from .faculty import parse_time
                        time_obj = parse_time(time_str)
                        if time_obj:
                            scheduled_datetime = datetime.strptime(scheduled_date_str, '%Y-%m-%d').replace(
                                hour=time_obj.hour, minute=time_obj.minute
                            )
                            slot_key = (discipline, scheduled_date_str, scheduled_datetime)
                            if slot_key in self.slot_assignments:
                                del self.slot_assignments[slot_key]
                    except (ValueError, AttributeError):
                        pass
                
                # Remove from applicant_slots
                if applicant_id in self.applicant_slots:
                    del self.applicant_slots[applicant_id]
        
        # Remove mismatched records from scheduled list
        for record in to_remove:
            if record in self.scheduled:
                self.scheduled.remove(record)


def format_scheduled_output(
    scheduled: List[Dict[str, Any]],
    mapper: Any,
    original_columns: List[str],
    existing_date_col: Optional[str] = None,
    existing_time_col: Optional[str] = None,
    existing_order_col: Optional[str] = None,
    breaks: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Format scheduled applicants for Excel output, including BREAK rows.
    
    Args:
        scheduled: List of scheduled applicant dicts
        mapper: ColumnMapper instance
        original_columns: Original column names from input (preserves order)
        existing_date_col: Name of existing date column in input (if any)
        existing_time_col: Name of existing time column in input (if any)
        existing_order_col: Name of existing order column in input (if any)
        breaks: List of break info dicts with 'discipline', 'date', 'type', 'start', 'end'
        
    Returns:
        List of dicts ready for Excel output, with columns in original_columns order
        Includes BREAK rows interspersed with scheduled applicants
    """
    output = []
    
    # Internal field names used by the scheduler
    internal_date = 'Music Audition Date'
    internal_time = 'Music Audition Time'
    internal_order = 'Music Audition Order'
    
    for record in scheduled:
        # Get denormalized data (may not be in correct order)
        denormalized = mapper.denormalize_applicant(record)
        
        # Build row dict in the exact order of original_columns
        # This ensures output columns match input column order exactly
        row = {}
        for col_name in original_columns:
            # If this column is one of the audition columns, fill it with scheduled data
            if col_name == existing_date_col:
                row[col_name] = record.get(internal_date, "")
            elif col_name == existing_time_col:
                row[col_name] = record.get(internal_time, "")
            elif col_name == existing_order_col:
                row[col_name] = record.get(internal_order, "")
            else:
                # Use value from denormalized data
                row[col_name] = denormalized.get(col_name, "")
        
        # Only add scheduling fields at the end if they don't already exist in original_columns
        if not existing_date_col:
            row[internal_date] = record.get(internal_date, '')
        if not existing_time_col:
            row[internal_time] = record.get(internal_time, '')
        if not existing_order_col:
            row[internal_order] = record.get(internal_order, '')
        
        output.append(row)
    
    # Create BREAK rows if breaks are provided
    if breaks:
        from .faculty import parse_time
        
        # Find the major/discipline column name once
        major_col = None
        for col in original_columns:
            col_lower = col.lower()
            if 'major' in col_lower or ('discipline' in col_lower and 'department' not in col_lower):
                major_col = col
                break
        
        # If no major column found, check mapper for the normalized field name
        if not major_col:
            try:
                major_field = mapper.get_applicant_column('major')
                if major_field:
                    for col in original_columns:
                        if col == major_field:
                            major_col = col
                            break
            except:
                pass
        
        # Last resort: use first column as fallback
        if not major_col and original_columns:
            major_col = original_columns[0]
        
        for break_info in breaks:
            discipline = break_info.get('discipline', '')
            date_str = break_info.get('date', '')
            break_type = break_info.get('type', 'break')
            break_start = break_info.get('start')
            break_end = break_info.get('end')
            
            if not (discipline and date_str and break_start):
                continue
            
            # Find the last scheduled applicant before this break
            # This determines where the break should appear in the order
            last_order_before_break = 0
            if isinstance(break_start, datetime):
                for row in output:
                    if row.get('_is_break'):
                        continue  # Skip other breaks
                    
                    # Check if same discipline and date
                    row_discipline = row.get(major_col, '') if major_col else ''
                    row_date = row.get(internal_date) or row.get(existing_date_col, '')
                    
                    if row_discipline == discipline and row_date == date_str:
                        # Parse the time for this applicant
                        time_str = row.get(internal_time) or row.get(existing_time_col, '')
                        if time_str:
                            time_obj = parse_time(time_str)
                            if time_obj:
                                # Create datetime for comparison
                                try:
                                    row_dt = datetime.strptime(date_str, '%Y-%m-%d').replace(
                                        hour=time_obj.hour, minute=time_obj.minute
                                    )
                                    # If this applicant is scheduled before the break, track their order
                                    if row_dt < break_start:
                                        order_val = row.get(internal_order) or row.get(existing_order_col)
                                        if order_val:
                                            try:
                                                order_int = int(order_val) if not isinstance(order_val, int) else order_val
                                                last_order_before_break = max(last_order_before_break, order_int)
                                            except (ValueError, TypeError):
                                                pass
                                except ValueError:
                                    pass
            
            # Assign break order as fractional value after the last applicant
            # e.g., if last applicant is 8, break becomes 8.5
            break_order = last_order_before_break + 0.5 if last_order_before_break > 0 else 0.5
            
            # Create a BREAK row
            break_row = {}
            for col_name in original_columns:
                if col_name == major_col:
                    # Set discipline name so BREAK rows sort with that discipline
                    break_row[col_name] = discipline
                elif col_name == existing_date_col or col_name == 'Music Audition Date':
                    break_row[col_name] = date_str
                elif col_name == existing_time_col or col_name == 'Music Audition Time':
                    # Format break time (use start time)
                    if isinstance(break_start, datetime):
                        break_row[col_name] = break_start.strftime('%I:%M %p').lstrip('0')
                    else:
                        break_row[col_name] = str(break_start)
                elif col_name == existing_order_col or col_name == 'Music Audition Order':
                    # BREAK rows get fractional order (e.g., 8.5 after applicant #8)
                    break_row[col_name] = break_order
                else:
                    # For other columns, use "BREAK" in identifying fields
                    col_lower = col_name.lower()
                    if 'slate' in col_lower or 'id' in col_lower:
                        # Application Slate ID or similar ID fields
                        break_row[col_name] = "BREAK"
                    elif 'last' in col_lower or 'first' in col_lower or 'name' in col_lower:
                        # Name fields - use BREAK for visibility
                        break_row[col_name] = "BREAK"
                    else:
                        break_row[col_name] = ""
            
            # Add scheduling fields if they don't exist
            if not existing_date_col:
                break_row[internal_date] = date_str
            if not existing_time_col:
                if isinstance(break_start, datetime):
                    break_row[internal_time] = break_start.strftime('%I:%M %p').lstrip('0')
                else:
                    break_row[internal_time] = str(break_start)
            if not existing_order_col:
                break_row[internal_order] = break_order
            
            # Add a note about break type
            break_row['_is_break'] = True
            break_row['_break_type'] = break_type
            
            output.append(break_row)
    
    # Sort by Music Audition Order only
    # Music Audition Order already encodes: degree precedence → date → time
    # BREAK rows have fractional orders (e.g., 8.5) to appear in chronological position
    def get_sort_key(row: Dict[str, Any]) -> Tuple[str, float]:
        """Get sort key for proper ordering: discipline → Music Audition Order."""
        # Get discipline/major for grouping (so each instrument is grouped together)
        major_col = None
        for col in original_columns:
            if 'major' in col.lower() or ('discipline' in col.lower() and 'department' not in col.lower()):
                major_col = col
                break
        
        discipline = row.get(major_col, '') if major_col else ''
        
        # Get Music Audition Order (can be int or float for BREAK rows)
        # Music Audition Order already includes degree precedence (BM first, then MM, etc.)
        order_value = row.get(internal_order) or row.get(existing_order_col)
        if order_value is None or order_value == "":
            order_num = 999998.0  # Unscheduled rows at end
        else:
            try:
                order_num = float(order_value)
            except (ValueError, TypeError):
                order_num = 999998.0
        
        return (discipline, order_num)
    
    output.sort(key=get_sort_key)
    
    return output


