# Audition Scheduler UI

Electron desktop application for the Audition Scheduler.

## For End Users

The packaged application is a standalone installer that includes:
- Electron runtime
- React frontend
- Bundled Python runtime with all dependencies
- Pre-configured school settings

**No Python installation required!** Just download, install, and run.

See [TESTER_INSTRUCTIONS.md](TESTER_INSTRUCTIONS.md) for user documentation.

## Development

### Prerequisites
- Node.js 18+
- Python 3.8+ (for development only)

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

3. Install Python package (for development):
```bash
cd ..
pip install -e .
cd electron
```

4. Build TypeScript:
```bash
npm run build:main
```

5. Start development:
```bash
npm run dev
```

This will:
- Start Vite dev server for the React app (port 5173)
- Launch Electron window
- Enable hot reload

## Building for Distribution

### Full Bundle (Recommended)

Creates a standalone installer with bundled Python:

```bash
# From project root
./scripts/build-all.sh --mac    # For macOS
./scripts/build-all.sh --win    # For Windows
./scripts/build-all.sh --linux  # For Linux
```

Or from the electron directory:
```bash
npm run dist          # Full bundled build
npm run dist:mac      # macOS only
```

See [PACKAGING.md](PACKAGING.md) for detailed build instructions.

## Project Structure

- `main/` - Electron main process (TypeScript)
- `renderer/` - React frontend application
  - `src/components/` - React components
  - `src/lib/config.ts` - School configuration (hardcoded for each school)
  - `src/lib/store.ts` - State management
- `resources/` - Bundled resources (Python executable, etc.)
- `scripts/` - Build scripts

## Features

- File upload (drag & drop + file picker)
- Configuration validation before scheduling
- Calendar configuration
- Run scheduler with progress feedback
- View results (schedule, conflicts, metrics)
- Download output files
- Dark/light theme toggle

## School Configuration

The app is configured for a specific school at build time. Configuration is in:
- `renderer/src/lib/config.ts` - School name and config file paths

To create a build for a different school:
1. Update `SCHOOL` and `SCHOOL_CONFIG` in `config.ts`
2. Add the school's configuration files to `schools/{school_name}/`
3. Build and package

## Developer Settings

Advanced settings are hidden from regular users but accessible via keyboard shortcut:
- **Ctrl+Shift+S** (Windows/Linux) or **Cmd+Shift+S** (Mac)

This allows developers to browse for custom configuration files during debugging.
