# Quick Start Guide

## Prerequisites

1. **Node.js 18+** installed
2. **Python 3.8+** with the `audish` package installed
   ```bash
   cd ..  # Go to project root
   pip install -e .
   ```

## First Time Setup

1. Install dependencies:
   ```bash
   cd electron
   npm install
   cd renderer
   npm install
   cd ..
   ```

2. Build TypeScript:
   ```bash
   npm run build:main
   ```

## Running the App

```bash
npm run dev
```

This will:
- Start the Vite dev server (React frontend)
- Launch the Electron window
- Enable hot reload for development

## Building for Production

```bash
npm run build
```

This builds both the main process and renderer.

## Usage

1. **Upload Files**: Click or drag & drop your Excel files:
   - Applicant Info file
   - Faculty Availability file

2. **Configure Calendar**: 
   - Add audition days with start/end times
   - Or load from existing `rules.yaml`

3. **Select Configuration Files**:
   - Mapping file (default: `schools/juilliard/mapping.yaml`)
   - Rules file (default: `schools/juilliard/rules.yaml`)

4. **Run Scheduler**: Click "Run Scheduler" button

5. **View Results**: 
   - See metrics summary
   - Browse scheduled applicants
   - Review conflicts
   - Download output files

## Troubleshooting

- **Python not found**: Make sure Python is in your PATH
- **Module not found**: Ensure `audish` package is installed (`pip install -e .` from project root)
- **Port 5173 in use**: Stop other Vite dev servers or change port in `vite.config.ts`

