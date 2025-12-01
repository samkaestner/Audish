"""
Core scheduling algorithm.
Implements greedy assignment with constraints, conflict tracking, and numbering.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
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
        
        # Order applicants by: degree precedence → fewest valid slots → stable ID
        applicant_slots.sort(key=lambda x: (
            self.rules.get_degree_rank(x['applicant'].get('degree', '')),
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
                # Add to conflicts
                reason = reason_codes.NO_VALID_SLOTS if not valid_slots else reason_codes.CAPACITY_EXCEEDED
                self._add_conflict(applicant, reason, "No available slots matching all constraints")
    
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
        
        valid_slots = []
        
        # Generate slots for each calendar day
        for day in self.rules.get_calendar_days():
            date_str = day['date'] if isinstance(day['date'], str) else day['date'].strftime('%Y-%m-%d')
            
            # Generate slots for this discipline/degree/day
            slots = self.rules.generate_slots(discipline, degree, date_str, applicant_count=100)
            
            for start_time, end_time in slots:
                # Check teacher presence
                teacher_rank = self._check_teacher_presence(
                    teacher1, teacher2, teacher3, date_str, start_time
                )
                
                # Apply teacher presence policy
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
        scheduled_record['Music Audition Time'] = start_time.strftime('%H:%M')
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
                scheduled_hour, scheduled_min = map(int, scheduled_time_str.split(':'))
                scheduled_datetime = slot_start.replace(hour=scheduled_hour, minute=scheduled_min)
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
        
        Args:
            applicant: Applicant dict
            reason_code: Reason code constant
            details: Human-readable details
        """
        self.conflicts.append({
            'ApplicantID': applicant.get('id', ''),
            'Degree': applicant.get('degree', ''),
            'Discipline': applicant.get('major') or applicant.get('department', ''),
            'ReasonCode': reason_code,
            'Details': details
        })
    
    def _number_auditions(self) -> None:
        """
        Assign sequential Music Audition Order per discipline across all days.
        """
        # Group by discipline
        by_discipline = defaultdict(list)
        for scheduled in self.scheduled:
            discipline = scheduled.get('_discipline', '')
            if discipline:
                by_discipline[discipline].append(scheduled)
        
        # Number each discipline
        for discipline, records in by_discipline.items():
            # Sort by date, then time
            records.sort(key=lambda x: (
                x.get('Music Audition Date', ''),
                x.get('Music Audition Time', '')
            ))
            
            # Assign sequential numbers
            for order, record in enumerate(records, start=1):
                record['Music Audition Order'] = order


def format_scheduled_output(
    scheduled: List[Dict[str, Any]],
    mapper: Any,
    original_columns: List[str]
) -> List[Dict[str, Any]]:
    """
    Format scheduled applicants for Excel output.
    
    Args:
        scheduled: List of scheduled applicant dicts
        mapper: ColumnMapper instance
        original_columns: Original column names from input
        
    Returns:
        List of dicts ready for Excel output
    """
    output = []
    
    for record in scheduled:
        # Start with denormalized original data
        row = mapper.denormalize_applicant(record)
        
        # Add scheduling fields
        row['Music Audition Date'] = record.get('Music Audition Date', '')
        row['Music Audition Time'] = record.get('Music Audition Time', '')
        row['Music Audition Order'] = record.get('Music Audition Order', '')
        
        output.append(row)
    
    return output


