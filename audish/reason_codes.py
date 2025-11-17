"""
Conflict reason codes and human-readable descriptions.
"""

# Reason code constants
NO_VALID_SLOTS = "NO_VALID_SLOTS"
TEACHER_UNAVAILABLE = "TEACHER_UNAVAILABLE"
CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
DOUBLE_MAJOR_OVERLAP = "DOUBLE_MAJOR_OVERLAP"
SCHEDULING_ERROR = "SCHEDULING_ERROR"
FACULTY_CONSTRAINT_FAILED = "FACULTY_CONSTRAINT_FAILED"
TIME_CONSTRAINT_FAILED = "TIME_CONSTRAINT_FAILED"

# Human-readable descriptions
REASON_DESCRIPTIONS = {
    NO_VALID_SLOTS: "No slots available that match all constraints",
    TEACHER_UNAVAILABLE: "Required teacher(s) not available on any day",
    CAPACITY_EXCEEDED: "All available slots at capacity",
    DOUBLE_MAJOR_OVERLAP: "Timing conflict with applicant's other audition(s)",
    SCHEDULING_ERROR: "Unexpected error during scheduling",
    FACULTY_CONSTRAINT_FAILED: "Faculty presence requirements not met",
    TIME_CONSTRAINT_FAILED: "Applicant availability constraints not satisfied",
}


def get_reason_description(reason_code: str) -> str:
    """
    Get human-readable description for a reason code.
    
    Args:
        reason_code: The reason code constant
        
    Returns:
        Human-readable description
    """
    return REASON_DESCRIPTIONS.get(reason_code, f"Unknown reason: {reason_code}")




