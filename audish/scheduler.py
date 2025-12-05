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
        
        # State for strict degree ordering
        current_degree_rank = -1
        strict_ordering_cutoff: Optional[datetime] = None
        discipline_max_end_time: Optional[datetime] = None
        
        # Greedy assignment
        for item in applicant_slots:
            applicant = item['applicant']
            valid_slots = item['valid_slots']
            
            # Check for degree rank change
            degree_rank = self.rules.get_degree_rank(applicant.get('degree', ''))
            if degree_rank > current_degree_rank:
                if current_degree_rank != -1:
                    # Update cutoff for lower priority degrees
                    # Strict ordering: subsequent degrees must start after all previous degree slots end
                    strict_ordering_cutoff = discipline_max_end_time
                current_degree_rank = degree_rank
            
            # Filter valid slots if strict ordering is in effect
            if strict_ordering_cutoff:
                # Only consider slots that start at or after the cutoff time
                # (i.e. after the latest slot used by higher priority degrees)
                valid_slots = [
                    s for s in valid_slots 
                    if s['start'] >= strict_ordering_cutoff
                ]
            
            assigned = False
            for slot_info in valid_slots:
                if self._try_assign_slot(applicant, discipline, slot_info):
                    assigned = True
                    
                    # Update max end time for this discipline
                    slot_end = slot_info['end']
                    if discipline_max_end_time is None or slot_end > discipline_max_end_time:
                        discipline_max_end_time = slot_end
                        
                    break
            
            if not assigned:
                # Check if registration date is missing - only flag if registration date field is configured
                if self.registration_date_field:
                    registration_date_str = self._parse_registration_date(applicant)
                    if registration_date_str is None:
                        self._add_conflict(
                            applicant,
                            reason_codes.REGISTRATION_DATE_MISSING,
                            "Registration date is missing from applicant data - cannot schedule"
                        )
                        continue
                
                # Determine conflict reason
                teacher1 = applicant.get('teacher1')
                teacher2 = applicant.get('teacher2')
                teacher3 = applicant.get('teacher3')
                has_teacher_preferences = bool(teacher1 or teacher2 or teacher3)
                degree = applicant.get('degree', 'MM')
                
                if not valid_slots:
                    # Check if it's because no teachers are available
                    if has_teacher_preferences:
                        # Check if any day has teacher availability
                        has_any_teacher_availability = False
                        for day in self.rules.get_calendar_days():
                            date_str = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
                            # Generate a sample slot to check teacher availability
                            sample_slots = self.rules.generate_slots(discipline, degree, date_str, applicant_count=1)
                            if sample_slots:
                                sample_start = sample_slots[0][0]
                                teacher_rank = self._check_teacher_presence(
                                    teacher1, teacher2, teacher3, date_str, sample_start
                                )
                                if teacher_rank > 0:
                                    has_any_teacher_availability = True
                                    break
                        
                        if not has_any_teacher_availability:
                            reason = reason_codes.TEACHER_UNAVAILABLE
                            teacher_list = [t for t in [teacher1, teacher2, teacher3] if t]
                            details = f"None of the preferred teachers ({', '.join(teacher_list)}) are available on any scheduled day"
                        else:
                            reason = reason_codes.NO_VALID_SLOTS
                            details = "No available slots matching all constraints"
                    else:
                        reason = reason_codes.NO_VALID_SLOTS
                        details = "No available slots matching all constraints"
                else:
                    reason = reason_codes.CAPACITY_EXCEEDED
                    details = "All available slots at capacity"
                
                self._add_conflict(applicant, reason, details)
    
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
        
        valid_slots = []
        
        # Generate slots for each calendar day
        for day in self.rules.get_calendar_days():
            date_str = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
            
            # If applicant has a registration date, only consider slots on that date
            if registration_date_str and date_str != registration_date_str:
                continue
            
            # Generate slots for this discipline/degree/day
            slots = self.rules.generate_slots(discipline, degree, date_str, applicant_count=100)
            
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
        """
        from .faculty import parse_time
        
        def get_sort_key(record: Dict[str, Any]) -> Tuple[str, datetime]:
            """Create a sort key that properly handles 12-hour time format."""
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
                    return (date_str, dt)
                except ValueError:
                    pass
            
            # Fallback: use a very late datetime to push invalid entries to the end
            return (date_str, datetime.max)
        
        # Group by discipline
        by_discipline = defaultdict(list)
        for scheduled in self.scheduled:
            discipline = scheduled.get('_discipline', '')
            if discipline:
                by_discipline[discipline].append(scheduled)
        
        # Number each discipline
        for discipline, records in by_discipline.items():
            # Sort by date, then time (using proper datetime parsing)
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
                
                # Try common date formats
                formats = [
                    '%Y-%m-%d',      # 2025-02-28
                    '%m/%d/%Y',      # 2/28/2025
                    '%m-%d-%Y',      # 2-28-2025
                    '%Y/%m/%d',      # 2025/02/28
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
    existing_order_col: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Format scheduled applicants for Excel output.
    
    Args:
        scheduled: List of scheduled applicant dicts
        mapper: ColumnMapper instance
        original_columns: Original column names from input (preserves order)
        existing_date_col: Name of existing date column in input (if any)
        existing_time_col: Name of existing time column in input (if any)
        existing_order_col: Name of existing order column in input (if any)
        
    Returns:
        List of dicts ready for Excel output, with columns in original_columns order
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
    
    return output


