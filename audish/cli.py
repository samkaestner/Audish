"""
CLI entrypoint using Click.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

import click

from .io_excel import read_excel_sheet, write_schedule_excel, write_conflicts_excel, get_date_columns
from .mapping import ColumnMapper
from .faculty import build_faculty_availability
from .faculty_names import (
    build_faculty_name_map, get_all_faculty_names, 
    diagnose_teacher_matching
)
from .rules import RulesEngine
from .scheduler import Scheduler, format_scheduled_output


@click.group()
def cli():
    """Audish - Audition Scheduler CLI"""
    pass


@cli.command()
@click.option('--app', required=True, type=click.Path(exists=True), help='Applicants Excel file')
@click.option('--fac', required=True, type=click.Path(exists=True), help='Faculty availability Excel file')
@click.option('--map', 'mapping_file', required=True, type=click.Path(exists=True), help='Mapping YAML file')
@click.option('--rules', 'rules_file', required=True, type=click.Path(exists=True), help='Rules YAML file')
@click.option('--out-schedule', required=True, type=click.Path(), help='Output schedule Excel file')
@click.option('--out-conflicts', required=True, type=click.Path(), help='Output conflicts Excel file')
@click.option('--out-metrics', type=click.Path(), help='Output metrics text file (optional, defaults to stdout)')
def schedule(app, fac, mapping_file, rules_file, out_schedule, out_conflicts, out_metrics):
    """
    Schedule auditions from Excel inputs to Excel outputs.
    """
    click.echo("=" * 60)
    click.echo("Audish - Audition Scheduler")
    click.echo("=" * 60)
    
    # 1. Load configuration
    click.echo("\n[1/7] Loading configuration...")
    try:
        mapper = ColumnMapper(mapping_file)
        rules_engine = RulesEngine(rules_file)
        click.echo(f"  ✓ Loaded mapping: {mapping_file}")
        click.echo(f"  ✓ Loaded rules: {rules_file}")
        click.echo(f"  ✓ Teacher presence policy: {rules_engine.teacher_presence_policy}")
        click.echo(f"  ✓ Degree precedence: {' → '.join(rules_engine.degree_precedence)}")
    except Exception as e:
        click.echo(f"  ✗ Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # 2. Load applicants
    click.echo("\n[2/7] Loading applicants...")
    try:
        app_sheet_name = mapper.get_applicant_sheet_name()
        original_columns, app_rows = read_excel_sheet(app, app_sheet_name)
        applicants = [mapper.normalize_applicant(row) for row in app_rows]
        # Filter out empty rows
        applicants = [a for a in applicants if a.get('id')]
        click.echo(f"  ✓ Loaded {len(applicants)} applicants from '{app_sheet_name}'")
        
        # Show discipline breakdown
        disciplines = Counter(a.get('major') or a.get('department') for a in applicants)
        click.echo(f"  ✓ Disciplines: {len(disciplines)} unique")
        for disc, count in disciplines.most_common(5):
            click.echo(f"    • {disc}: {count}")
        if len(disciplines) > 5:
            click.echo(f"    • ... and {len(disciplines) - 5} more")
    except Exception as e:
        click.echo(f"  ✗ Error loading applicants: {e}", err=True)
        sys.exit(1)
    
    # 3. Load faculty availability
    click.echo("\n[3/7] Loading faculty availability...")
    try:
        fac_sheet_name = mapper.get_faculty_sheet_name()
        fac_columns, fac_rows = read_excel_sheet(fac, fac_sheet_name)
        faculty_records = [mapper.normalize_faculty(row) for row in fac_rows]
        
        # Auto-detect date columns
        date_columns = get_date_columns(fac, fac_sheet_name)
        click.echo(f"  ✓ Loaded {len(faculty_records)} faculty records")
        click.echo(f"  ✓ Detected {len(date_columns)} date columns")
        if date_columns:
            click.echo(f"    • Date range: {date_columns[0]} to {date_columns[-1]}")
    except Exception as e:
        click.echo(f"  ✗ Error loading faculty: {e}", err=True)
        sys.exit(1)
    
    # 4. Build faculty name mapping
    click.echo("\n[4/7] Building faculty name mapping...")
    try:
        faculty_names = get_all_faculty_names(faculty_records, 'faculty_name')
        faculty_name_aliases = mapper.get_faculty_name_aliases()
        faculty_name_map = build_faculty_name_map(faculty_names, faculty_name_aliases)
        click.echo(f"  ✓ Built name mapping for {len(faculty_names)} faculty members")
        
        # Diagnose teacher matching
        match_stats = diagnose_teacher_matching(applicants, faculty_name_map)
        if match_stats['total_teacher_preferences'] > 0:
            click.echo(f"  ✓ Teacher name match rate: {match_stats['match_rate']:.1f}%")
            if match_stats['unmatched'] > 0:
                click.echo(f"  ⚠ {match_stats['unmatched']} unmatched teacher preferences")
                if len(match_stats['unmatched_names']) <= 5:
                    for name in list(match_stats['unmatched_names'])[:5]:
                        click.echo(f"    • {name}")
    except Exception as e:
        click.echo(f"  ✗ Error building faculty name mapping: {e}", err=True)
        sys.exit(1)
    
    # 5. Parse faculty availability
    click.echo("\n[5/7] Parsing faculty availability...")
    try:
        calendar_days = rules_engine.get_calendar_days()
        faculty_availability = build_faculty_availability(
            faculty_records,
            date_columns,
            'faculty_name',
            'notes',
            calendar_days
        )
        available_faculty = len([f for f in faculty_availability if faculty_availability[f]])
        click.echo(f"  ✓ Parsed availability for {available_faculty} faculty members")
    except Exception as e:
        click.echo(f"  ✗ Error parsing faculty availability: {e}", err=True)
        sys.exit(1)
    
    # 6. Run scheduler
    click.echo("\n[6/7] Running scheduler...")
    try:
        scheduler = Scheduler(rules_engine, faculty_availability, applicants, mapper, faculty_name_map)
        scheduled, conflicts = scheduler.schedule()
        click.echo(f"  ✓ Scheduled: {len(scheduled)} applicants")
        click.echo(f"  ✓ Conflicts: {len(conflicts)} applicants")
    except Exception as e:
        click.echo(f"  ✗ Error during scheduling: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 7. Write output files
    click.echo("\n[7/7] Writing output files...")
    try:
        # Detect existing audition columns in the input file (with or without "Music" prefix)
        # Map internal field names to possible column names in the file
        audition_date_fields = ["Music Audition Date", "Audition Date"]
        audition_time_fields = ["Music Audition Time", "Audition Time"]
        audition_order_fields = ["Music Audition Order", "Audition Order"]
        
        # Find which columns exist in the original file
        existing_date_col = next((col for col in original_columns if col in audition_date_fields), None)
        existing_time_col = next((col for col in original_columns if col in audition_time_fields), None)
        existing_order_col = next((col for col in original_columns if col in audition_order_fields), None)
        
        # Format scheduled output - use original_columns as-is (columns will be filled in place)
        scheduled_output = format_scheduled_output(
            scheduled, 
            mapper, 
            original_columns,
            existing_date_col,
            existing_time_col,
            existing_order_col
        )
        
        # Write schedule - use original_columns to preserve exact order
        write_schedule_excel(out_schedule, original_columns, scheduled_output)
        click.echo(f"  ✓ Wrote schedule: {out_schedule}")
        
        # Write conflicts
        write_conflicts_excel(out_conflicts, conflicts)
        click.echo(f"  ✓ Wrote conflicts: {out_conflicts}")
    except Exception as e:
        click.echo(f"  ✗ Error writing output: {e}", err=True)
        sys.exit(1)
    
    # 8. Generate and display metrics
    click.echo("\n[8/8] Generating metrics...")
    try:
        metrics_text = generate_metrics(applicants, scheduled, conflicts)
        
        if out_metrics:
            Path(out_metrics).parent.mkdir(parents=True, exist_ok=True)
            with open(out_metrics, 'w') as f:
                f.write(metrics_text)
            click.echo(f"  ✓ Wrote metrics: {out_metrics}")
        
        click.echo("\n" + "=" * 60)
        click.echo("METRICS")
        click.echo("=" * 60)
        click.echo(metrics_text)
    except Exception as e:
        click.echo(f"  ✗ Error generating metrics: {e}", err=True)
    
    # Exit code
    if len(scheduled) == 0:
        click.echo("\n⚠️  WARNING: Zero applicants scheduled!", err=True)
        sys.exit(1)
    else:
        click.echo(f"\n✓ Success! Scheduled {len(scheduled)}/{len(applicants)} applicants.")
        sys.exit(0)


def generate_metrics(
    applicants: list,
    scheduled: list,
    conflicts: list
) -> str:
    """
    Generate human-readable metrics report.
    
    Args:
        applicants: All applicants
        scheduled: Successfully scheduled applicants
        conflicts: Conflict records
        
    Returns:
        Formatted metrics string
    """
    lines = []
    
    # Overall statistics
    total = len(applicants)
    scheduled_count = len(scheduled)
    conflict_count = len(conflicts)
    fill_rate = (scheduled_count / total * 100) if total > 0 else 0
    
    lines.append(f"Overall Statistics")
    lines.append(f"  Total Applicants:     {total}")
    lines.append(f"  Scheduled:            {scheduled_count}")
    lines.append(f"  Conflicts:            {conflict_count}")
    lines.append(f"  Fill Rate:            {fill_rate:.1f}%")
    lines.append("")
    
    # Teacher preference match
    teacher_ranks = [s.get('_teacher_rank', 0) for s in scheduled]
    first_choice = sum(1 for r in teacher_ranks if r == 3)
    second_choice = sum(1 for r in teacher_ranks if r == 2)
    third_choice = sum(1 for r in teacher_ranks if r == 1)
    no_preference = sum(1 for r in teacher_ranks if r == 0)
    
    first_choice_pct = (first_choice / scheduled_count * 100) if scheduled_count > 0 else 0
    
    lines.append(f"Teacher Preference Match")
    lines.append(f"  1st Choice:           {first_choice} ({first_choice_pct:.1f}%)")
    lines.append(f"  2nd Choice:           {second_choice}")
    lines.append(f"  3rd Choice:           {third_choice}")
    lines.append(f"  No Preference:        {no_preference}")
    lines.append("")
    
    # Conflicts by reason
    if conflicts:
        reason_counts = Counter(c.get('ReasonCode', 'UNKNOWN') for c in conflicts)
        lines.append(f"Conflicts by Reason")
        for reason, count in reason_counts.most_common():
            lines.append(f"  {reason}: {count}")
        lines.append("")
    
    # Per-discipline counts
    discipline_scheduled = defaultdict(int)
    discipline_total = defaultdict(int)
    
    for applicant in applicants:
        disc = applicant.get('major') or applicant.get('department', 'Unknown')
        discipline_total[disc] += 1
    
    for record in scheduled:
        disc = record.get('_discipline', 'Unknown')
        discipline_scheduled[disc] += 1
    
    lines.append(f"Per-Discipline Breakdown")
    for disc in sorted(discipline_total.keys()):
        sched = discipline_scheduled[disc]
        total_disc = discipline_total[disc]
        pct = (sched / total_disc * 100) if total_disc > 0 else 0
        lines.append(f"  {disc}: {sched}/{total_disc} ({pct:.1f}%)")
    
    return "\n".join(lines)


if __name__ == '__main__':
    cli()


