# Packaging Guide

This guide explains how to package the Audition Scheduler UI for distribution.

## Quick Start (Recommended)

The recommended approach bundles Python with the Electron app, so users don't need to install Python separately.

### One-Command Build

```bash
# From the project root directory
./scripts/build-all.sh --mac    # For macOS
./scripts/build-all.sh --win    # For Windows
./scripts/build-all.sh --linux  # For Linux
./scripts/build-all.sh --all    # For all platforms
```

This script:
1. ✅ Bundles Python + all dependencies using PyInstaller
2. ✅ Builds the Electron app
3. ✅ Packages everything into a standalone installer

### From the Electron Directory

```bash
cd electron
npm run dist          # Full bundled build (recommended)
npm run dist:mac      # macOS only
npm run dist:win      # Windows only
npm run dist:linux    # Linux only
```

## Output

Packages will be created in `electron/dist/`:
- **macOS**: `Audition Scheduler-1.0.0.dmg` and `.zip`
- **Windows**: `Audition Scheduler Setup 1.0.0.exe` and portable version
- **Linux**: `audition-scheduler-ui-1.0.0.AppImage` and `.deb`

## What Gets Bundled

### Full Bundle (Recommended)
- ✅ Electron runtime
- ✅ React frontend (built)
- ✅ TypeScript main process (compiled)
- ✅ Python runtime (bundled via PyInstaller)
- ✅ `audish` Python package + all dependencies
- ✅ School configuration files (YAML)

**Users don't need to install anything - just run the app!**

### Development/Testing Build (Without Python Bundle)

For development or quick testing, you can package without bundling Python:

```bash
cd electron
npm run package:mac      # macOS (.dmg, .zip)
npm run package:win      # Windows (.exe installer, portable)
npm run package:linux    # Linux (.AppImage, .deb)
```

⚠️ **Note**: This requires users to have Python 3.8+ and the `audish` package installed.

## Build Requirements

### For Bundled Build (Recommended)

- **Python 3.8+** - Required to build the bundled executable
- **pip** - For installing PyInstaller and dependencies
- **Node.js 18+** - For building the Electron app
- **npm** - For package management

### For Quick Testing Build

- **Node.js 18+** - For building the Electron app
- **npm** - For package management

## Manual Build Steps

If you need more control over the build process:

### Step 1: Build Python Executable

```bash
# From project root
./scripts/build-python.sh

# On Windows:
scripts\build-python.bat
```

This creates `dist/audish` (or `dist/audish.exe` on Windows).

### Step 2: Copy to Electron Resources

```bash
mkdir -p electron/resources
cp dist/audish electron/resources/audish-cli
# On Windows: copy dist\audish.exe electron\resources\audish-cli.exe
```

### Step 3: Build Electron App

```bash
cd electron
npm run build
```

### Step 4: Package

```bash
npm run package:mac    # or :win, :linux, :all
```

## Testing the Package

### Before Distribution

1. **Test on a clean machine** (or VM):
   - Install the packaged app
   - Run without any Python/audish installation
   - Verify file upload works
   - Verify scheduler runs successfully
   - Verify output files are created

2. **Test file paths**:
   - Try with files in different locations
   - Test drag & drop
   - Test file picker
   - Test saving output files

3. **Test error handling**:
   - Invalid Excel files
   - Missing required columns
   - Empty files

## Distribution Checklist

- [ ] Run full bundled build (`./scripts/build-all.sh`)
- [ ] Test on clean machine without Python installed
- [ ] Verify bundled scheduler works correctly
- [ ] Test file upload functionality
- [ ] Test scheduler execution
- [ ] Test download functionality
- [ ] Verify school configurations are bundled
- [ ] Test with sample data files

## Troubleshooting

### PyInstaller Build Fails

```bash
# Clean build artifacts and retry
./scripts/build-python.sh --clean
```

### "Python not found" in Development Mode

In development mode (non-packaged), the app falls back to system Python:

```bash
# Install Python 3.8+
# macOS: brew install python@3.11
# Windows: Download from python.org

# Install audish package
pip install -e .
```

### Large Package Size

The bundled Python runtime adds approximately 50-100MB to the package size. This is expected and includes:
- Python interpreter
- openpyxl (Excel handling)
- click (CLI framework)
- PyYAML (configuration)
- python-dateutil (date parsing)

### Code Signing (macOS)

For distribution outside the Mac App Store:

```yaml
# In electron-builder.yml
mac:
  hardenedRuntime: true
  entitlements: build/entitlements.mac.plist
```

## Version Updates

To update the version:
1. Edit `electron/package.json` version field
2. Rebuild and repackage
3. Update `TESTER_INSTRUCTIONS.md` if needed

## Architecture Notes

### How Python Bundling Works

1. **PyInstaller** bundles the Python interpreter, all dependencies, and the `audish` package into a single executable (`audish-cli`)

2. **Electron Builder** includes this executable in the app's `resources` directory

3. **At runtime**, the Electron app:
   - Checks if it's running in packaged mode
   - If packaged: Uses the bundled `audish-cli` executable
   - If development: Falls back to system `python3`

### File Locations (Packaged App)

```
Audition Scheduler.app/
├── Contents/
│   ├── MacOS/
│   │   └── Audition Scheduler     # Electron main process
│   └── Resources/
│       ├── app.asar               # Bundled Electron app
│       ├── audish-cli             # Bundled Python executable
│       └── schools/               # Configuration files
│           └── juilliard/
│               ├── mapping.yaml
│               └── rules.yaml
```
