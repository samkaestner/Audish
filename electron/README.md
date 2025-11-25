# Audition Scheduler UI

Electron desktop application for the Audition Scheduler.

## Development

### Prerequisites
- Node.js 18+
- Python 3.8+ with audish package installed

### Setup

1. Install root dependencies:
```bash
cd electron
npm install
```

2. Install renderer dependencies:
```bash
cd renderer
npm install
cd ..
```

3. Build TypeScript:
```bash
npm run build:main
```

4. Start development:
```bash
npm run dev
```

This will:
- Start Vite dev server for the React app (port 5173)
- Launch Electron window
- Enable hot reload

## Building

```bash
npm run build
```

This builds both the main process TypeScript and the renderer React app.

## Project Structure

- `main/` - Electron main process (TypeScript)
- `renderer/` - React frontend application
  - `src/components/` - React components
  - `src/lib/` - Utilities and store

## Features

- File upload (drag & drop + file picker)
- Calendar configuration
- Run scheduler
- View results (schedule, conflicts, metrics)
- Download output files

