Audition Scheduler — Project Knowledge File (Excel‑in/Excel‑out, Stateless)

This file is your single source of truth for building a stateless, single‑user batch scheduler that:

reads two Excel workbooks (Applicants & Faculty Availability),

applies Juilliard audition rules plus faculty/applicant availability,

outputs a final Excel with Music Audition Date, Music Audition Time, and instrument‑scoped sequential Music Audition Order (continues across days),

produces a Conflicts report with reason codes.

It is designed so you can adapt to other schools later by swapping in mapping.yaml and rules.yaml.

0) Scope & Operating Model

No database. Single admissions user uploads two spreadsheets and downloads the result.

Batch, deterministic scheduling on demand (same inputs ⇒ same outputs).

All Slate I/O via Excel (no APIs in v1).

Security: local/offline processing preferred; if web, ephemeral storage and auto‑delete after run.

1) Inputs (Excel)

A) Faculty Availability (FA25 Faculty Avail.xlsx)

Sheet name (example): Sheet1 (support arbitrary name via mapping.yaml).

Columns (observed): DEPT, Faculty, Preferred, date columns (e.g., 2025‑02‑28, 2025‑03‑01, … 2025‑03‑07), Notes.

Semantics:

A date column marks presence/absence for that day (cell can be truthy, time‑window text, or blank).

Preferred (boolean/text) indicates a faculty member’s preferred audition days.

Notes may contain constraints like: “after 1pm only”, “no Friday”, “11:00–15:00”.

B) Applicants (Applicant Info No Times.xlsx)

Sheet name (example): Export (support arbitrary name via mapping.yaml).

Columns (observed from Slate export):

Identity & status: Last, First, Preferred, Juilliard Status, BM and BCJ Applicant, Audition Modality Accommodation Approved.

Program: Degree Level (BM/MM/GD/AD/DMA/BCJ), Department (Application), Major (Application), Voice Type.

Teacher prefs: 1st Choice Teacher, 2nd Choice Teacher, 3rd Choice Teacher.

School: School 1 Organization.

Event fields: Event – Most Recent Registration Status, Event – Most Recent Registration Event Date/Time (read‑only for us in v1).

Unique key: Applicant ID (exact column name varies by export; map in mapping.yaml).

⚠️ Do not assume canonical column names. All real column names are defined in mapping.yaml so the tool is Slate‑export‑proof.

2) Outputs (Excel)

FinalSchedule.xlsx (sheet: Schedule)

All original applicant columns (preserved order), plus three appended fields:

Music Audition Date  (YYYY‑MM‑DD)

Music Audition Time  (HH:MM, institution local time)

Music Audition Order (instrument‑scoped, sequential across days)e.g., Violin might run 1…67…N with Day 3 beginning at 67.

Optional Notes column describing placement decisions: e.g., TeacherRank=2; Avoided same‑school adjacency.

Conflicts.xlsx (sheet: Conflicts)For applicants not placed, with fields: ApplicantID, Degree, Discipline, ReasonCode, Details.

Metrics.txt (optional)Human‑readable summary: fill rate, % 1st‑choice, conflicts by reason, per‑instrument counts.

3) Rules & Priorities

Represent rules in an external rules.yaml so you can adapt per school.

Hard constraints (never violate)

Slot capacity & time bounds.

Applicant cannot overlap their own times; double‑major auditions must not overlap.

Faculty/teacher presence requirement (configurable per discipline).

Room/instrument suitability if provided (organ/harp/percussion flags).

Priority objectives (optimize; can fall back)

Degree precedence: BM → MM/GD → AD → DMA (MM/GD must be before AD/DMA within a discipline).

Teacher preference: 1st → 2nd → 3rd.

Same‑school spacing: avoid back‑to‑back from the same School 1 Organization (unless current Juilliard student).

Pack days cleanly while respecting breaks/special patterns (e.g., Oboe 12‑minute open).

Discipline cadence examples (non‑exhaustive)

Cello — BM: 5/hr (3 at :00; 2 at :30); MM–DMA: every 15m.

Oboe — 5/hr with one 12‑minute open per hour.

Flute — 7/hr; callbacks 8/hr (pilot may skip callbacks).

French Horn (Recorded) — every 15m; insert 15m break every 5–6 applicants.

Percussion — BM 20m; MM–DMA 30m; reserve 1h discussion at end of final day.

Keep all cadence/break patterns declarative in rules.yaml.

4) Scheduling Windows

Define audition date range & daily hours in rules.yaml, e.g.:
calendar:
  timezone: "America/New_York"
  days:
    - date: 2025-02-28
      start: "09:00"
      end:   "17:00"
      lunch: ["12:30","13:30"]
    - date: 2025-03-01
      start: "09:00"
      end:   "17:00"

      Faculty sheet provides day‑level presence; Notes may refine to sub‑day windows (e.g., after 13:00, 10:00–14:00).

Applicant availability (if provided) can further narrow valid windows.

5) Configuration Files

mapping.yaml (example)
applicants:
  sheet: "Export"
  columns:
    id: "Applicant ID"     # exact column name from Slate export; update as needed
    last: "Last"
    first: "First"
    preferred_name: "Preferred"
    degree: "Degree Level"
    department: "Department (Application)"
    major: "Major (Application)"
    voice_type: "Voice Type"
    teacher1: "1st Choice Teacher"
    teacher2: "2nd Choice Teacher"
    teacher3: "3rd Choice Teacher"
    school_org: "School 1 Organization"
    juilliard_status: "Juilliard Status"
    bm_bcj_flag: "BM and BCJ Applicant"
    modality_accommodation: "Audition Modality Accommodation Approved"
faculty:
  sheet: "Sheet1"
  columns:
    dept: "DEPT"
    faculty_name: "Faculty"
    preferred_flag: "Preferred"
    notes: "Notes"
    # Date columns are auto‑detected as those with datetime column headers

    