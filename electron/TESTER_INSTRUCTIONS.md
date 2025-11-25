# Audition Scheduler - Tester Instructions

Thank you for testing the Audition Scheduler application!

## Prerequisites

Before running the application, you need to install Python and the scheduler package:

### 1. Install Python

- **macOS**: Python should already be installed. Verify with `python3 --version` (should be 3.8+)
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Usually pre-installed, or install via package manager

### 2. Install the Audition Scheduler Package

1. Download or clone the entire `Audition_Scheduler` project folder
2. Open Terminal/Command Prompt
3. Navigate to the project root directory:
   ```bash
   cd /path/to/Audition_Scheduler
   ```
4. Install the package:
   ```bash
   pip install -e .
   ```
   (or `pip3 install -e .` on macOS/Linux if `pip` doesn't work)

5. Verify installation:
   ```bash
   audish --help
   ```
   You should see help text for the scheduler CLI.

## Installing the UI Application

### macOS
1. Open the `.dmg` file
2. Drag "Audition Scheduler" to Applications
3. Open from Applications (you may need to right-click and select "Open" the first time due to security)

### Windows
1. Run the `.exe` installer
2. Follow the installation wizard
3. Launch from Start Menu or desktop shortcut

### Linux
1. For `.deb`: `sudo dpkg -i Audition-Scheduler-*.deb`
2. For `.AppImage`: Make executable (`chmod +x`) and double-click

## Using the Application

### 1. Prepare Your Files

You'll need two Excel files:
- **Applicant Info file**: Contains applicant data (from Slate export)
- **Faculty Availability file**: Contains faculty availability schedule

### 2. Launch the Application

Open "Audition Scheduler" from your applications menu.

### 3. Upload Files

- Click or drag & drop your Excel files into the upload areas
- Select your Applicant Info file
- Select your Faculty Availability file

### 4. Configure Calendar

- The app will try to load days from `schools/juilliard/rules.yaml` automatically
- Click "Add Day" to add new audition days
- Set start and end times for each day
- You can edit or remove days as needed

### 5. Select Configuration Files (Optional)

- Defaults to `schools/juilliard/mapping.yaml` and `schools/juilliard/rules.yaml`
- Click "Browse" to select different files if needed

### 6. Run the Scheduler

- Click the large "Run Scheduler" button
- Wait for processing (may take a few moments)
- Results will appear below

### 7. View Results

- **Metrics**: Summary statistics at the top
- **Schedule tab**: View scheduled applicants
- **Conflicts tab**: View applicants that couldn't be scheduled
- **Metrics tab**: Full metrics report

### 8. Download Results

- Click "Download Excel" buttons to save output files
- Files will be saved to your chosen location

## Troubleshooting

### "Python not found" error
- Make sure Python is installed and in your PATH
- Try running `python --version` or `python3 --version` in terminal

### "Module not found" or "audish not found" error
- Make sure you've installed the package: `pip install -e .` from project root
- Verify with: `audish --help`

### Application won't start
- Check that you have Node.js 18+ installed (for development builds)
- Try running from terminal to see error messages

### Excel files not loading
- Verify files are `.xlsx` or `.xls` format
- Check that files aren't corrupted
- Make sure you have read permissions

### Scheduler fails to run
- Check that both Excel files are selected
- Verify at least one audition day is configured
- Check the error message for specific issues

## Reporting Issues

When reporting issues, please include:
1. Your operating system (macOS/Windows/Linux)
2. Python version (`python --version`)
3. Steps to reproduce the issue
4. Any error messages shown
5. Screenshots if helpful

## Files Created

The scheduler creates output files in the `output/` directory:
- `FinalSchedule.xlsx` - Scheduled applicants
- `Conflicts.xlsx` - Applicants that couldn't be scheduled
- `Metrics.txt` - Summary statistics

These can be downloaded from the UI or found in the project's `output/` folder.

