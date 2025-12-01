# Audition Scheduler - Tester Instructions

Thank you for testing the Audition Scheduler application!

## Installation

The application is a standalone installer that includes everything you need - **no Python installation required**.

### macOS
1. Open the `.dmg` file (named `Audition Scheduler-1.0.0-arm64.dmg` or similar)
2. Drag "Audition Scheduler" to Applications
3. Open from Applications (you may need to right-click and select "Open" the first time due to macOS security)

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
- **Faculty Availability file**: Contains faculty availability schedule with date columns

### 2. Launch the Application

Open "Audition Scheduler" from your applications menu.

### 3. Upload Files

- Click or drag & drop your Excel files into the upload areas
- Select your Applicant Info file
- Select your Faculty Availability file

The app is pre-configured for your school's data format - no need to select configuration files!

### 4. Validate Configuration (Optional but Recommended)

Click **"Validate Configuration"** to check your files before running:
- Verifies Excel columns match expected format
- Checks that all applicant disciplines have scheduling rules
- Shows helpful error messages if anything needs fixing

### 5. Configure Calendar

- The app will try to load audition days from the configuration automatically
- Click "Add Day" to add new audition days
- Set start and end times for each day
- You can edit or remove days as needed

### 6. Run the Scheduler

- Click the **"Run Scheduler"** button
- Wait for processing (may take a few moments depending on dataset size)
- Results will appear below

### 7. View Results

- **Metrics**: Summary statistics at the top
- **Schedule tab**: View scheduled applicants
- **Conflicts tab**: View applicants that couldn't be scheduled
- **Metrics tab**: Full metrics report

### 8. Download Results

- Click "Download Excel" buttons to save output files
- Files will be saved to your chosen location

## Output Files

The scheduler creates three files:
- **FinalSchedule.xlsx** - Scheduled applicants with dates, times, and order numbers
- **Conflicts.xlsx** - Applicants that couldn't be scheduled (with reasons)
- **Metrics.txt** - Summary statistics

## Troubleshooting

### Application won't start
- On macOS: Right-click and select "Open" if you see a security warning
- Try restarting your computer and launching again

### Excel files not loading
- Verify files are `.xlsx` format (not `.xls` or `.csv`)
- Check that files aren't corrupted or open in another program
- Make sure you have read permissions

### Validation fails
- Read the error messages carefully - they explain exactly what needs fixing
- Common issues:
  - Column names in Excel don't match expected format
  - Missing scheduling rules for certain disciplines
  - Sheet names are different than expected

### Scheduler fails to run
- Run validation first to catch configuration issues
- Check that both Excel files are selected
- Verify at least one audition day is configured
- Check the error message for specific issues

## Developer Access

For advanced configuration (debugging only), press **Ctrl+Shift+S** (or **Cmd+Shift+S** on Mac) to access developer settings.

## Reporting Issues

When reporting issues, please include:
1. Your operating system (macOS/Windows/Linux)
2. Steps to reproduce the issue
3. Any error messages shown (screenshots are helpful)
4. The validation results if applicable
