"""
API routes for Audish scheduling.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from io import StringIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse

# Add parent directory to path to import audish package
sys.path.insert(0, str(Path(__file__).parent.parent))

from audish.io_excel import read_excel_sheet, write_schedule_excel, write_conflicts_excel, get_date_columns
from audish.mapping import ColumnMapper
from audish.rules import RulesEngine
from audish.scheduler import Scheduler, format_scheduled_output
from audish.faculty import build_faculty_availability
from audish.faculty_names import build_faculty_name_map, get_all_faculty_names

router = APIRouter()

# Hardcoded paths to configuration files
MAPPING_PATH = Path(__file__).parent.parent / "schools" / "juilliard" / "mapping.yaml"
RULES_PATH = Path(__file__).parent.parent / "schools" / "juilliard" / "rules.yaml"


@router.post("/validate-files")
async def validate_files(
    request: Request,
    applicants: UploadFile = File(...),
    faculty: UploadFile = File(...),
):
    """
    Validate uploaded Excel files and return preview data.
    """
    try:
        temp_dir = request.app.state.temp_dir

        # Save uploaded files temporarily
        applicants_path = os.path.join(temp_dir, "applicants.xlsx")
        faculty_path = os.path.join(temp_dir, "faculty.xlsx")

        with open(applicants_path, "wb") as f:
            content = await applicants.read()
            f.write(content)

        with open(faculty_path, "wb") as f:
            content = await faculty.read()
            f.write(content)

        # Load configuration
        mapper = ColumnMapper(str(MAPPING_PATH))

        # Read and validate applicants file
        try:
            app_columns, app_records = read_excel_sheet(applicants_path)
            app_records = mapper.normalize_applicants(app_columns, app_records)
            # Filter empty rows
            app_records = [r for r in app_records if r.get("id")]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading applicants file: {str(e)}")

        # Read and validate faculty file
        try:
            fac_columns, fac_records = read_excel_sheet(faculty_path, sheet_name="Sheet1")
            fac_records = mapper.normalize_faculty(fac_columns, fac_records)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading faculty file: {str(e)}")

        # Calculate statistics
        disciplines = {}
        for record in app_records:
            discipline = record.get("major") or record.get("department") or "Unknown"
            disciplines[discipline] = disciplines.get(discipline, 0) + 1

        degrees = {}
        for record in app_records:
            degree = record.get("degree", "Unknown")
            degrees[degree] = degrees.get(degree, 0) + 1

        # Get sample data for preview (first 10 records)
        app_preview = app_records[:10]
        fac_preview = fac_records[:10]

        # Extract faculty names for name matching validation
        all_faculty_names = get_all_faculty_names(app_records)

        # Build faculty name mapping
        faculty_names = [r.get("faculty_name", "") for r in fac_records]
        faculty_name_aliases = mapper.config.get("faculty_name_aliases", {})
        name_mapping = build_faculty_name_map(faculty_names, faculty_name_aliases)

        # Count matched vs unmatched
        matched_count = 0
        for teacher_name in all_faculty_names:
            normalized = teacher_name.lower().strip()
            if normalized in name_mapping:
                matched_count += 1

        unmatched_count = len(all_faculty_names) - matched_count
        match_rate = ((matched_count) / len(all_faculty_names) * 100) if all_faculty_names else 100

        warnings = []
        if match_rate < 90:
            warnings.append(f"Faculty name match rate is {match_rate:.1f}%. Some teachers may not be matched correctly.")

        return {
            "success": True,
            "applicants": {
                "total": len(app_records),
                "preview": app_preview,
                "disciplines": disciplines,
                "degrees": degrees,
            },
            "faculty": {
                "total": len(fac_records),
                "preview": fac_preview,
            },
            "validation": {
                "faculty_match_rate": round(match_rate, 1),
                "matched_faculty": len(all_faculty_names) - unmatched_count,
                "total_faculty": len(all_faculty_names),
                "warnings": warnings,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/schedule")
async def schedule(
    request: Request,
    applicants: UploadFile = File(...),
    faculty: UploadFile = File(...),
):
    """
    Run the scheduling algorithm and return results with metrics.
    """
    try:
        temp_dir = request.app.state.temp_dir

        # Save uploaded files
        applicants_path = os.path.join(temp_dir, "applicants.xlsx")
        faculty_path = os.path.join(temp_dir, "faculty.xlsx")

        with open(applicants_path, "wb") as f:
            content = await applicants.read()
            f.write(content)

        with open(faculty_path, "wb") as f:
            content = await faculty.read()
            f.write(content)

        # Output file paths
        schedule_path = os.path.join(temp_dir, "FinalSchedule.xlsx")
        conflicts_path = os.path.join(temp_dir, "Conflicts.xlsx")

        # Load configuration
        mapper = ColumnMapper(str(MAPPING_PATH))
        rules = RulesEngine(str(RULES_PATH))

        # Read applicants
        app_columns, app_records = read_excel_sheet(applicants_path)
        app_records = mapper.normalize_applicants(app_columns, app_records)
        app_records = [r for r in app_records if r.get("id")]

        # Read faculty
        fac_columns, fac_records = read_excel_sheet(faculty_path, sheet_name="Sheet1")
        fac_records = mapper.normalize_faculty(fac_columns, fac_records)

        # Get date columns
        date_columns = get_date_columns(fac_columns)

        # Build faculty name mapping
        all_faculty_names = get_all_faculty_names(app_records)
        faculty_names = [r.get("faculty_name", "") for r in fac_records]
        faculty_name_aliases = mapper.config.get("faculty_name_aliases", {})
        faculty_name_map = build_faculty_name_map(faculty_names, faculty_name_aliases)

        # Parse faculty availability
        calendar_days = rules.get_calendar_days()
        faculty_availability = build_faculty_availability(
            fac_records,
            date_columns,
            'faculty_name',
            'notes',
            calendar_days
        )

        # Run scheduler
        scheduler = Scheduler(
            rules,
            faculty_availability,
            app_records,
            mapper,
            faculty_name_map
        )

        scheduled, conflicts = scheduler.schedule()

        # Generate metrics
        metrics = _generate_metrics(scheduled, conflicts, app_records)

        # Format and write output files
        formatted_scheduled = format_scheduled_output(scheduled, app_records)
        write_schedule_excel(formatted_scheduled, app_columns, mapper, schedule_path)
        write_conflicts_excel(conflicts, conflicts_path)

        # Return results with preview data
        scheduled_preview = scheduled[:50]  # First 50 for preview
        conflicts_preview = conflicts[:50]

        return {
            "success": True,
            "metrics": metrics,
            "scheduled": {
                "total": len(scheduled),
                "preview": scheduled_preview,
                "download_url": "/api/download/FinalSchedule.xlsx"
            },
            "conflicts": {
                "total": len(conflicts),
                "preview": conflicts_preview,
                "download_url": "/api/download/Conflicts.xlsx"
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scheduling error: {str(e)}")


@router.get("/download/{filename}")
async def download_file(request: Request, filename: str):
    """
    Download generated Excel files.
    """
    temp_dir = request.app.state.temp_dir
    file_path = os.path.join(temp_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def _generate_metrics(scheduled: List[Dict], conflicts: List[Dict], all_applicants: List[Dict]) -> Dict[str, Any]:
    """
    Generate metrics similar to the CLI output.
    """
    total = len(all_applicants)
    scheduled_count = len(scheduled)
    conflicts_count = len(conflicts)
    fill_rate = (scheduled_count / total * 100) if total > 0 else 0

    # Teacher preference match rates
    teacher_matches = {"1st": 0, "2nd": 0, "3rd": 0, "none": 0}
    for record in scheduled:
        matched = record.get("matched_teacher_choice", "none")
        if matched in teacher_matches:
            teacher_matches[matched] += 1
        else:
            teacher_matches["none"] += 1

    # Conflicts by reason
    conflict_reasons = {}
    for conflict in conflicts:
        reason = conflict.get("reason_code", "UNKNOWN")
        conflict_reasons[reason] = conflict_reasons.get(reason, 0) + 1

    # Per-discipline breakdown
    discipline_stats = {}
    for record in all_applicants:
        discipline = record.get("major") or record.get("department") or "Unknown"
        if discipline not in discipline_stats:
            discipline_stats[discipline] = {"total": 0, "scheduled": 0, "conflicts": 0}
        discipline_stats[discipline]["total"] += 1

    for record in scheduled:
        discipline = record.get("major") or record.get("department") or "Unknown"
        if discipline in discipline_stats:
            discipline_stats[discipline]["scheduled"] += 1

    for conflict in conflicts:
        discipline = conflict.get("discipline", "Unknown")
        if discipline in discipline_stats:
            discipline_stats[discipline]["conflicts"] += 1

    return {
        "overall": {
            "total": total,
            "scheduled": scheduled_count,
            "conflicts": conflicts_count,
            "fill_rate": round(fill_rate, 1)
        },
        "teacher_preferences": teacher_matches,
        "conflict_reasons": conflict_reasons,
        "by_discipline": discipline_stats
    }
