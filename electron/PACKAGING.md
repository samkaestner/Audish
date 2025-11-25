# Packaging Guide

This guide explains how to package the Audition Scheduler UI for distribution.

## Quick Start

### For Testing (Single Platform)

```bash
cd electron
./package-for-testing.sh
```

This will automatically detect your platform and create the appropriate packages.

### Manual Packaging

```bash
cd electron

# Build the application first
npm run build

# Package for specific platforms
npm run package:mac      # macOS (.dmg, .zip)
npm run package:win      # Windows (.exe installer, portable)
npm run package:linux    # Linux (.AppImage, .deb)
npm run package:all      # All platforms
```

## Output

Packages will be created in `electron/dist/`:
- **macOS**: `Audition Scheduler-1.0.0.dmg` and `.zip`
- **Windows**: `Audition Scheduler Setup 1.0.0.exe` and portable version
- **Linux**: `audition-scheduler-ui-1.0.0.AppImage` and `.deb`

## What Gets Packaged

The packaged application includes:
- ✅ Electron runtime
- ✅ React frontend (built)
- ✅ TypeScript main process (compiled)
- ❌ Python runtime (testers must install separately)
- ❌ `audish` Python package (testers must install separately)

## Important Notes

### Python Dependency

The packaged app **requires** Python and the `audish` package to be installed on the tester's machine. The app calls Python as a subprocess to run the scheduler.

**Before distributing:**
1. Share `TESTER_INSTRUCTIONS.md` with testers
2. Ensure testers install Python 3.8+
3. Ensure testers install `audish` package (`pip install -e .`)

### File Paths

The app expects to find:
- Configuration files: `schools/juilliard/mapping.yaml` and `rules.yaml`
- These should be in the project root, not packaged with the app
- Testers need access to the full project folder OR you can bundle these files

### Alternative: Bundle Everything

If you want to avoid Python setup, consider:
1. Creating a standalone Python executable using PyInstaller
2. Bundling Python with the Electron app (larger package size)
3. Using a web-based API instead of local Python calls

## Testing the Package

Before distributing:

1. **Test on clean machine** (or VM):
   - Install only Python + audish package
   - Run the packaged app
   - Verify file upload works
   - Verify scheduler runs successfully

2. **Test file paths**:
   - Try with files in different locations
   - Test drag & drop
   - Test file picker

3. **Test error handling**:
   - Missing Python
   - Missing audish package
   - Invalid Excel files
   - Missing configuration files

## Distribution Checklist

- [ ] Built application (`npm run build`)
- [ ] Created packages (`npm run package`)
- [ ] Tested on clean machine
- [ ] Created `TESTER_INSTRUCTIONS.md` (already done)
- [ ] Verified Python/audish installation steps work
- [ ] Tested file upload functionality
- [ ] Tested scheduler execution
- [ ] Tested download functionality
- [ ] Shared installer + instructions with testers

## Version Updates

To update the version:
1. Edit `package.json` version field
2. Rebuild and repackage
3. Update `TESTER_INSTRUCTIONS.md` if needed

