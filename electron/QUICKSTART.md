# Quick Start Guide

## For End Users

### Installation

1. Download the installer for your platform:
   - **macOS**: `Audition Scheduler-X.X.X-arm64.dmg`
   - **Windows**: `Audition Scheduler Setup X.X.X.exe`
   - **Linux**: `Audition-Scheduler-X.X.X.AppImage` or `.deb`

2. Install the application:
   - **macOS**: Open DMG, drag to Applications
   - **Windows**: Run installer, follow wizard
   - **Linux**: Run AppImage or install deb package

3. Launch and use! No additional setup required.

### Usage

1. **Upload Files**: Click or drag & drop your Excel files:
   - Applicant Info file (from Slate export)
   - Faculty Availability file

2. **Validate** (recommended): Click "Validate Configuration" to check files

3. **Configure Calendar**: Add or edit audition days

4. **Run Scheduler**: Click "Run Scheduler" button

5. **Download Results**: Save the output Excel files

---

## For Developers

### Prerequisites

- Node.js 18+
- Python 3.8+ with audish package installed

### First Time Setup

```bash
# From project root
pip install -e .

# Install dependencies
cd electron
npm install
cd renderer
npm install
cd ..

# Build TypeScript
npm run build:main
```

### Running the App

```bash
npm run dev
```

This will:
- Start the Vite dev server (React frontend)
- Launch the Electron window
- Enable hot reload for development

### Building for Distribution

```bash
# From project root - builds with bundled Python
./scripts/build-all.sh --mac
```

Or from electron directory:
```bash
npm run dist:mac
```

See [PACKAGING.md](PACKAGING.md) for full build instructions.

### Developer Settings

Hidden settings are accessible via **Ctrl+Shift+S** (or **Cmd+Shift+S** on Mac) for debugging.

## Troubleshooting

- **Port 5173 in use**: Stop other Vite dev servers or change port in `vite.config.ts`
- **Python errors in dev mode**: Ensure `audish` package is installed (`pip install -e .` from project root)
- **Module not found**: Make sure all npm dependencies are installed
