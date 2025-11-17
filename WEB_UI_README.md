# Audish Web UI

A modern web interface for the Audish audition scheduling system.

## Features

- **Drag & Drop File Upload**: Easily upload applicant and faculty Excel files
- **File Validation**: Preview and validate uploaded data before scheduling
- **Real-time Scheduling**: Run the scheduling algorithm with a single click
- **Interactive Dashboard**: View comprehensive metrics and statistics
- **Results Preview**: Browse scheduled applicants and conflicts in the browser
- **Excel Download**: Download final schedule and conflicts as Excel files

## Quick Start

### Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)

### Running the Application

#### On Mac/Linux:

```bash
./start.sh
```

#### On Windows:

Double-click `start.bat` or run from command prompt:

```cmd
start.bat
```

The script will:
1. Install all necessary dependencies
2. Start the backend API server (port 8000)
3. Start the frontend web server (port 3000)
4. Open your browser automatically to http://localhost:3000

## How to Use

### Step 1: Upload Files

1. **Upload Applicant Information**: Drag and drop or browse for your applicants Excel file
2. **Upload Faculty Availability**: Drag and drop or browse for your faculty availability Excel file

### Step 2: Validate

Click the **"Validate Files"** button to:
- Check file formats
- Preview data
- View statistics (total applicants, disciplines, faculty match rate)
- See any warnings

### Step 3: Schedule

After validation, click the **"Run Scheduler"** button to:
- Execute the scheduling algorithm
- Generate audition schedules
- Identify conflicts

### Step 4: Review Results

The dashboard will display:
- **Overall Metrics**: Total, scheduled, conflicts, fill rate
- **Teacher Preferences**: How many applicants got their 1st, 2nd, 3rd choice teachers
- **Conflict Analysis**: Breakdown of why applicants couldn't be scheduled
- **Per-Discipline Stats**: Scheduling success rate by instrument/discipline

### Step 5: Download

Click the download buttons to get:
- **FinalSchedule.xlsx**: All successfully scheduled applicants with dates and times
- **Conflicts.xlsx**: List of applicants who couldn't be scheduled with reasons

## Configuration

The application uses hardcoded configuration files from:
- `schools/juilliard/mapping.yaml` - Column mappings and name aliases
- `schools/juilliard/rules.yaml` - Scheduling rules and calendar

Future versions will support uploading custom configuration files and switching between schools.

## Troubleshooting

### Port Already in Use

If you see "Port already in use" errors:

**Backend (port 8000):**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000    # Windows (then use Task Manager)
```

**Frontend (port 3000):**
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :3000    # Windows (then use Task Manager)
```

### Files Not Uploading

- Ensure files are in `.xlsx` format (not `.xls` or `.csv`)
- Check file size (very large files may take longer to upload)
- Verify your network connection if using remote server

### Validation Errors

Common issues:
- **Missing columns**: Ensure your Excel files have the expected column headers
- **Empty data**: Check that your Excel sheets have data rows
- **Faculty name mismatch**: Low match rates indicate teacher names in applicant file don't match faculty file

### Scheduling Errors

If scheduling fails:
- Check the browser console (F12) for detailed error messages
- Verify the backend API is running (visit http://localhost:8000)
- Review the API logs in the terminal

## Technical Details

### Architecture

- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **Scheduling Engine**: Original Audish Python package (unchanged)

### API Endpoints

- `POST /api/validate-files` - Upload and validate Excel files
- `POST /api/schedule` - Run scheduling algorithm
- `GET /api/download/{filename}` - Download generated files

### File Storage

- Temporary files are stored in the system temp directory
- Files are automatically cleaned up when the API server stops
- Each session has its own isolated temp directory

## Development

### Manual Setup

If the startup scripts don't work, you can run the servers manually:

**Backend:**
```bash
cd api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements.txt
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd web
npm install
npm run dev
```

### Building for Production

```bash
cd web
npm run build
npm run start
```

For production deployment, consider using:
- **Frontend**: Vercel, Netlify, or any static hosting
- **Backend**: Docker, AWS Lambda, or any Python hosting

## Support

For issues or questions:
1. Check the main `README.md` for general Audish documentation
2. Review the `USER_GUIDE.md` for scheduling concepts
3. Check the browser console and terminal logs for errors

## License

Same as the main Audish project.
