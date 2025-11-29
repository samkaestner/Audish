# Audish User Guide

**Quick Start Guide for Scheduling Juilliard Auditions**

---

## What is Audish?

Audish is an automated scheduling tool that assigns audition times to applicants based on:
- Faculty availability
- Instrument/discipline scheduling rules
- Teacher preferences
- Degree level priorities

**Input:** Excel files with applicant data and faculty availability  
**Output:** Scheduled auditions with dates, times, and order numbers

---

## Desktop Application (Recommended)

The easiest way to use Audish is through the desktop application:

1. **Install the application** (download the installer for your platform)
2. **Upload your Excel files** (drag & drop or click to browse)
3. **Click "Validate Configuration"** to check your files
4. **Configure audition calendar** (add/edit days)
5. **Click "Run Scheduler"**
6. **Download results**

The desktop app is pre-configured for your school - no manual configuration needed!

See `electron/TESTER_INSTRUCTIONS.md` for detailed desktop app instructions.

---

## Command Line Quick Start (TL;DR)

For advanced users or automation:

1. **Install Python 3.8+** (if not already installed)
2. **Navigate to the Audish folder** in Terminal/Command Prompt
3. **Install:** 
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate` then `pip install -e .`
   - Mac/Linux: `make install` (or manual: `python3 -m venv .venv` then `source .venv/bin/activate` then `pip install -e .`)
4. **Activate virtual environment** (always do this before running)
5. **Validate:** `audish validate --app "YourApplicants.xlsx" --fac "YourFaculty.xlsx" --map schools/juilliard/mapping.yaml --rules schools/juilliard/rules.yaml`
6. **Run:** `audish schedule --app "YourApplicants.xlsx" --fac "YourFaculty.xlsx" --map schools/juilliard/mapping.yaml --rules schools/juilliard/rules.yaml --out-schedule output/FinalSchedule.xlsx --out-conflicts output/Conflicts.xlsx --out-metrics output/Metrics.txt`
7. **Check results** in the `output/` folder

---

## Prerequisites

- **Windows PC, Mac, or Linux** (works on all platforms)
- **Python 3.8 or higher** (check by running `python --version` or `python3 --version` in terminal/command prompt)
- **Terminal/Command Prompt access**
- Your Excel files ready:
  - Applicant list (from Slate export)
  - Faculty availability sheet

---

## Installation (One-Time Setup)

### Step 1: Check Python Installation

**On Windows:**
1. Open Command Prompt (search for "cmd" in Start menu)
2. Type: `python --version` or `py --version`
3. If you see Python 3.8 or higher, you're good to go!
4. If not, download Python from [python.org](https://www.python.org/downloads/)

**On Mac/Linux:**
1. Open Terminal
2. Type: `python3 --version`
3. If you see Python 3.8 or higher, you're good to go!
4. If not, install Python using your system's package manager

### Step 2: Navigate to the Audish Folder

**On Windows:**
```cmd
cd path\to\Audition_Scheduler
```
*(Replace `path\to\Audition_Scheduler` with the actual folder location)*

**On Mac/Linux:**
```bash
cd /path/to/Audition_Scheduler
```
*(Replace `/path/to/Audition_Scheduler` with the actual folder location)*

### Step 3: Install the Package

**Option A: Using Make (Mac/Linux only, or Windows with WSL/Git Bash)**

```bash
make install
```

**Option B: Manual Installation (All Platforms)**

**On Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

**On Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This creates a virtual environment and installs all dependencies. You'll see output about downloading packages - this is normal and takes ~1 minute.

### Step 4: Verify Installation

**On Windows:**
```cmd
.venv\Scripts\audish --help
```

**On Mac/Linux:**
```bash
.venv/bin/audish --help
```

You should see the help message with available commands.

---

## Running the Scheduler

### Step 1: Prepare Your Files

Before running, make sure you have:
- ✅ **Applicant Excel file** - Slate export with all applicant data
- ✅ **Faculty availability Excel file** - With date columns formatted as YYYY-MM-DD in the headers
- ✅ **Configuration files** (already included):
  - `schools/juilliard/mapping.yaml` - Maps Excel column names to the system
  - `schools/juilliard/rules.yaml` - Defines scheduling rules and calendar dates

**Important:** Place your Excel files in the main Audition_Scheduler folder, or note their full file paths.

#### File Format Requirements

**Applicant Excel File:**
- Must be in `.xlsx` format (Excel 2007+)
- Should contain a sheet with applicant data (usually named "Export" for Slate exports)
- Required columns: Applicant ID, Degree Level, Major/Discipline, Teacher preferences
- Column names must match what's defined in `schools/juilliard/mapping.yaml`

**Faculty Availability Excel File:**
- Must be in `.xlsx` format
- Must have date columns with headers formatted as `YYYY-MM-DD` (e.g., `2025-02-28`)
- Should include faculty names and availability notes
- Each date column indicates whether a faculty member is available on that date

### Step 2: Activate the Virtual Environment

**On Windows:**
```cmd
.venv\Scripts\activate
```

**On Mac/Linux:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` appear at the start of your command prompt.

### Step 3: Validate Configuration (Recommended)

Before running the scheduler, validate your configuration to catch errors early:

**On Windows:**
```cmd
audish validate --app "YOUR_APPLICANT_FILE.xlsx" --fac "YOUR_FACULTY_FILE.xlsx" --map schools/juilliard/mapping.yaml --rules schools/juilliard/rules.yaml
```

**On Mac/Linux:**
```bash
audish validate \
  --app "YOUR_APPLICANT_FILE.xlsx" \
  --fac "YOUR_FACULTY_FILE.xlsx" \
  --map schools/juilliard/mapping.yaml \
  --rules schools/juilliard/rules.yaml
```

**What validation checks:**
- ✅ YAML configuration files are properly formatted
- ✅ Excel column names match the mapping configuration
- ✅ All applicant disciplines have scheduling rules defined
- ✅ Calendar days are properly configured

**If validation fails:**
- Read the error messages - they explain exactly what's wrong
- Fix the issue in the relevant file (mapping.yaml, rules.yaml, or your Excel files)
- Run validation again until it passes

### Step 4: Run the Scheduler

**Option A: Using Make (Mac/Linux only, or Windows with WSL/Git Bash)**

```bash
make run
```

**Option B: Custom Command (All Platforms)**

Replace `YOUR_APPLICANT_FILE.xlsx` and `YOUR_FACULTY_FILE.xlsx` with your actual file names:

**On Windows:**
```cmd
audish schedule --app "YOUR_APPLICANT_FILE.xlsx" --fac "YOUR_FACULTY_FILE.xlsx" --map schools/juilliard/mapping.yaml --rules schools/juilliard/rules.yaml --out-schedule output/FinalSchedule.xlsx --out-conflicts output/Conflicts.xlsx --out-metrics output/Metrics.txt
```

**On Mac/Linux:**
```bash
audish schedule \
  --app "YOUR_APPLICANT_FILE.xlsx" \
  --fac "YOUR_FACULTY_FILE.xlsx" \
  --map schools/juilliard/mapping.yaml \
  --rules schools/juilliard/rules.yaml \
  --out-schedule output/FinalSchedule.xlsx \
  --out-conflicts output/Conflicts.xlsx \
  --out-metrics output/Metrics.txt
```

**Tip:** If your Excel files are in a different folder, use the full path:
- Windows: `--app "C:\Users\YourName\Documents\Applicants.xlsx"`
- Mac/Linux: `--app "/Users/YourName/Documents/Applicants.xlsx"`

### Step 5: Review Output

The scheduler creates an `output/` folder with three files:

1. **FinalSchedule.xlsx** - Your scheduled auditions
   - Contains all original applicant columns
   - Plus three new columns:
     - `Music Audition Date` (YYYY-MM-DD)
     - `Music Audition Time` (12-hour format with AM/PM, e.g., "9:00 AM", "2:30 PM")
     - `Music Audition Order` (sequential number per instrument)

2. **Conflicts.xlsx** - Any applicants that couldn't be scheduled
   - Includes reason codes and details
   - Should ideally be empty!

3. **Metrics.txt** - Summary statistics
   - Overall fill rate
   - Teacher preference matches
   - Per-discipline breakdown

---

## Understanding the Output

### Terminal Output

While running, you'll see progress messages:

```
============================================================
Audish - Audition Scheduler
============================================================

[0/8] Validating configuration...
  ✓ Configuration validated

[1/8] Loading configuration...
  ✓ Loaded mapping: schools/juilliard/mapping.yaml
  ✓ Loaded rules: schools/juilliard/rules.yaml
  ✓ Teacher presence policy: prefer
  ✓ Degree precedence: BM → MM → GD → AD → DMA

[2/8] Loading applicants...
  ✓ Loaded 1132 applicants from 'Export'
  ✓ Disciplines: 41 unique
    • Piano: 161
    • Violin: 160
    • Voice: 131
    • Cello: 75
    • Viola: 70
    • ... and 36 more

[3/7] Loading faculty availability...
  ✓ Loaded 134 faculty records
  ✓ Detected 8 date columns
    • Date range: 2025-02-28 to 2025-03-07

... (continues through all 7 steps)

✓ Success! Scheduled 1132/1132 applicants.
```

### Success Indicators

✅ **Good signs:**
- Fill rate close to 100%
- High percentage of 1st choice teacher matches
- Few or no conflicts

⚠️ **Warning signs:**
- Many conflicts (check reason codes)
- Low teacher match percentage (faculty names may not match)
- Missing disciplines in output

---

## Updating Configuration

Configuration files are in YAML format (text files). You can edit them with any text editor:
- **Windows:** Notepad, Notepad++, or VS Code
- **Mac:** TextEdit, VS Code, or any code editor
- **Linux:** nano, vim, or any text editor

**⚠️ Important:** Be careful with spacing and indentation in YAML files - they are sensitive to formatting!

### Calendar Dates and Times

Edit `schools/juilliard/rules.yaml` to update audition dates and times. Find the `calendar` section:

#### Basic Calendar Setup

```yaml
calendar:
  days:
    - { date: 2025-02-28, start: "09:00", end: "17:00" }
    - { date: 2025-03-01, start: "09:00", end: "17:00" }
    # Add more dates by copying the format above
```

**Key points:**
- Dates must be in `YYYY-MM-DD` format
- Times are in 24-hour format (`09:00` = 9:00 AM, `17:00` = 5:00 PM)
- Make sure these dates match the date columns in your faculty availability file

#### Global Time Defaults (All Days, All Disciplines)

If most auditions start at the same time (e.g., 10:00 AM) and end at the same time (e.g., 6:00 PM), you can set global defaults:

```yaml
calendar:
  # Set global defaults for all days and all disciplines
  default_start_time: "10:00"  # All auditions start at 10:00 AM
  default_end_time: "18:00"    # All auditions end at 6:00 PM
  
  days:
    - { date: 2025-02-28 }     # Uses global defaults (10:00-18:00)
    - { date: 2025-03-01 }     # Uses global defaults (10:00-18:00)
    - { date: 2025-03-02, start: "09:00", end: "17:00" }  # Overrides global defaults
```

**Benefits:**
- Set times once for all days and disciplines
- Individual days can still override if needed
- Saves time when most days have the same schedule

#### Per-Discipline Time Overrides

If specific instruments/disciplines need different start or end times, you can override them:

**Example 1: Override for entire discipline (all degrees)**
```yaml
rules:
  Violin:
    start_time: "10:00"  # Violin auditions start at 10:00 AM
    end_time: "18:00"    # Violin auditions end at 6:00 PM
    ALL: { cadence: { type: fixed_interval, minutes: 15 } }
```

**Example 2: Override for specific degree only**
```yaml
rules:
  Piano:
    BM: 
      start_time: "10:00"  # Piano BM starts at 10:00 AM
      end_time: "16:00"    # Piano BM ends at 4:00 PM
      cadence: { type: fixed_interval, minutes: 20 }
    MM: 
      # Piano MM uses calendar defaults (no override)
      cadence: { type: fixed_interval, minutes: 20 }
```

**Example 3: Partial override (only start or only end)**
```yaml
rules:
  Cello:
    start_time: "10:00"  # Only override start time, uses calendar end_time
    ALL: { cadence: { type: fixed_interval, minutes: 15 } }
```

**Priority Order:**
1. Degree-specific `start_time`/`end_time` (highest priority)
2. Discipline ALL `start_time`/`end_time`
3. Discipline-level `start_time`/`end_time`
4. Day-specific `start`/`end` (from calendar days)
5. Global calendar defaults `default_start_time`/`default_end_time` (lowest priority)

**When to use:**
- Most areas start at 10:00 AM or later → Use global calendar defaults
- Specific instruments need different times → Use per-discipline overrides
- Only certain degrees need different times → Use per-degree overrides

### Instrument Rules

Add or modify instrument scheduling rules in `schools/juilliard/rules.yaml`. Find the `rules` section:

```yaml
rules:
  Violin:
    BM:   { cadence: { type: per_hour, cap: 5, half_hour_distribution: [3,2] } }
    MM:   { cadence: { type: fixed_interval, minutes: 15 } }
```

**Common cadence types:**
- `per_hour`: Limits number per hour (e.g., 5 per hour)
- `fixed_interval`: Fixed minutes between slots (e.g., 15 minutes)

**When to update:** Only if you need to change how many applicants are scheduled per hour or the spacing between auditions for a specific instrument.

### Column Mappings

If your Slate export uses different column names, update `schools/juilliard/mapping.yaml`:

```yaml
applicants:
  columns:
    id: "Application Slate ID"  # Change to match your Excel column name
    degree: "Degree Level"
    # Update other column names as needed
```

**When to update:** 
- When Slate changes their export format
- When column names in your Excel file don't match what's in the mapping file
- If you see "Zero applicants scheduled" error

**How to find column names:**
1. Open your applicant Excel file
2. Look at the first row (headers)
3. Match those exact names in the mapping.yaml file

---

## Troubleshooting

### Installation Issues

**"python: command not found" or "python3: command not found"**
- **Windows:** Python may not be in your PATH. Try `py` instead of `python`, or reinstall Python and check "Add Python to PATH" during installation
- **Mac/Linux:** Install Python using your system's package manager (e.g., `brew install python3` on Mac)

**"pip: command not found"**
- Make sure you've activated the virtual environment (you should see `(.venv)` in your prompt)
- Try: `python -m pip install -e .` instead of `pip install -e .`

**"Permission denied" errors (Mac/Linux)**
- You may need to use `sudo`, but this is usually not necessary. Try installing without sudo first.

### Runtime Issues

**"Zero applicants scheduled"**

**Causes:**
- Wrong sheet name in mapping.yaml
- Applicant ID column name mismatch
- Empty Excel file
- File path is incorrect

**Fix:** 
1. Open your applicant Excel file
2. Check the actual sheet name (probably "Export")
3. Check the ID column name (probably "Application Slate ID")
4. Update `schools/juilliard/mapping.yaml` accordingly
5. Verify the file path in your command is correct (use full path if needed)

**"No faculty available" or "Low teacher match rate"**

**Causes:**
- Faculty names don't match between Excel files
- Date columns not detected
- Date format is incorrect

**Fix:**
- Ensure date columns are formatted as YYYY-MM-DD in headers (e.g., `2025-02-28`, not `2/28/2025` or `Feb 28, 2025`)
- The system automatically matches names with different titles (Dr., Prof., etc.)
- Check the match rate in step [4/7] of the output - should be >80%
- For edge cases (nicknames, spelling variations), add manual aliases to `mapping.yaml` (see FACULTY_NAME_MATCHING.md)

**"Many conflicts" or "Not enough slots"**

**Causes:**
- Not enough time slots for the number of applicants
- Too restrictive faculty constraints
- Calendar dates don't match faculty availability dates

**Fix:**
- Add more audition days in `rules.yaml`
- Extend daily hours (start earlier/end later) using:
  - Global calendar defaults (`default_start_time`/`default_end_time`)
  - Per-discipline time overrides (`start_time`/`end_time`)
  - Day-specific times in the calendar days list
- Switch from "require" to "prefer" teacher presence policy in `rules.yaml`
- Verify calendar dates in `rules.yaml` match the date columns in your faculty file

**"File not found" or "No such file or directory"**

**Causes:**
- File path is incorrect
- File doesn't exist at that location
- Wrong working directory

**Fix:**
- Use full file paths if files are in a different folder
- Check that file names match exactly (including `.xlsx` extension)
- Make sure you're in the correct directory when running the command
- On Windows, use forward slashes `/` or escaped backslashes `\\` in paths

---

## Testing Workflow

### 1. Test with Small Dataset

Start with a small test file (10-20 applicants) to verify everything works:
1. Create a test Excel file with a subset of applicants
2. Run the scheduler with your test file
3. Open the output files and verify the results manually

### 2. Test with Full Dataset

Once the small test works, run with your complete dataset:
1. Run the scheduler with your full applicant file
2. Check the metrics file:
   - **On Windows:** Open `output/Metrics.txt` in Notepad or any text editor
   - **On Mac/Linux:** Run `cat output/Metrics.txt` in terminal
3. Open `FinalSchedule.xlsx` in Excel and verify a few applicants manually

### 3. Validate Results

Check that:
- ✅ No time overlaps for the same instrument
- ✅ Sequential numbering per instrument (1, 2, 3, etc.)
- ✅ Degree precedence respected (BM applicants scheduled first, then MM/GD, then AD, then DMA)
- ✅ Times fall within the calendar hours specified in rules.yaml (or discipline-specific overrides)
- ✅ Teacher preferences are honored when possible
- ✅ Times respect global calendar defaults or discipline-specific overrides (if configured)

---

## Pre-Flight Checklist

Before running the scheduler with your actual data:

- [ ] Python 3.8+ is installed and working
- [ ] Audish is installed (see Installation section)
- [ ] Applicant Excel file is ready and in the correct format
- [ ] Faculty availability Excel file is ready with YYYY-MM-DD date columns
- [ ] `mapping.yaml` column names match your Excel file columns
- [ ] `rules.yaml` has the correct audition dates for your schedule
- [ ] Time overrides are configured correctly (if using global defaults or per-discipline overrides)
- [ ] **Run `audish validate` to check configuration** (catches errors before scheduling)
- [ ] You've tested with a small sample file first (recommended)
- [ ] You know where your output files will be saved (`output/` folder)

**Recommended:** 
1. Always run `audish validate` first to catch configuration errors
2. Test with a small subset (10-20 applicants) before running the full dataset

---

## Getting Help

### View Detailed Help

**On Windows:**
```cmd
audish schedule --help
```

**On Mac/Linux:**
```bash
audish schedule --help
```

This shows all available options and command-line arguments.

### Run Tests (Optional)

**On Mac/Linux (with Make):**
```bash
make test
```

**On Windows (manual):**
```cmd
.venv\Scripts\pytest tests\ -v
```

**On Mac/Linux (manual):**
```bash
.venv/bin/pytest tests/ -v
```

All tests should pass to verify the installation is working correctly.

### Common Commands

**Clean and Reinstall (if something goes wrong):**

**On Windows:**
```cmd
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

**On Mac/Linux (with Make):**
```bash
make clean
make install
```

**On Mac/Linux (manual):**
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Faculty Name Matching

The scheduler automatically matches teacher names between Excel sheets:
- **Faculty Availability**: `"John Smith"`
- **Applicant Preferences**: `"Dr. John Smith"`, `"Prof. John Smith"`

The system normalizes names by removing titles (Dr., Prof., Mr., Ms., etc.) and handles:
- ✅ Case differences
- ✅ Hyphenated names
- ✅ Apostrophes (O'Brien)
- ✅ Extra whitespace

**Check the match rate** in step [4/7] of the output:
```
[4/7] Building faculty name mapping...
  ✓ Teacher name match rate: 89.3%
  ⚠ 279 unmatched teacher preferences
```

For edge cases (nicknames, spelling variations), add manual aliases to `mapping.yaml`:
```yaml
faculty_name_aliases:
  "Bob Smith": "Robert Smith"
  "Yo-Yo Ma": "YoYo Ma"
```

**See FACULTY_NAME_MATCHING.md for complete details.**

---

## Key Takeaways

### What You Need to Know

1. **Always activate the virtual environment** before running the scheduler
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`

2. **File formats matter:**
   - Excel files must be `.xlsx` format
   - Date columns must be `YYYY-MM-DD` format
   - Column names must match `mapping.yaml`

3. **Test first:** Always run with a small sample (10-20 applicants) before processing the full dataset

4. **Check the output:**
   - `FinalSchedule.xlsx` - Your scheduled auditions
   - `Conflicts.xlsx` - Applicants that couldn't be scheduled (should be empty or minimal)
   - `Metrics.txt` - Summary statistics

5. **Common issues:**
   - Low match rate? Check faculty name matching
   - Many conflicts? Add more days or extend hours in `rules.yaml`
   - Zero applicants scheduled? Check `mapping.yaml` column names

### System Characteristics

- **Deterministic**: Same inputs always produce same outputs
- **Stateless**: No database, all data in Excel files
- **Local**: Runs on your machine, no internet required
- **Fast**: Schedules 1000+ applicants in seconds
- **Cross-platform**: Works on Windows, Mac, and Linux

### Getting More Help

- **Detailed help:** Run `audish schedule --help` to see all options
- **Technical details:** See `README.md` for architecture and algorithm details
- **Faculty matching:** See `FACULTY_NAME_MATCHING.md` for advanced name matching

---

**Ready to get started?** Follow the Quick Start section at the top of this guide!

