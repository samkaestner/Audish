#!/bin/bash

# Packaging script for Audition Scheduler UI
# Creates distributable packages for testing

set -e

echo "=========================================="
echo "Audition Scheduler - Packaging for Testing"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Must run from electron/ directory"
    exit 1
fi

# Build the application
echo "Step 1: Building application..."
npm run build

if [ $? -ne 0 ]; then
    echo "Error: Build failed"
    exit 1
fi

echo ""
echo "Step 2: Creating packages..."
echo ""

# Determine platform and package accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - Creating macOS packages..."
    npm run package -- --mac
    echo ""
    echo "✅ macOS packages created in dist/"
    echo "   - Look for .dmg and .zip files"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows - Creating Windows packages..."
    npm run package -- --win
    echo ""
    echo "✅ Windows packages created in dist/"
    echo "   - Look for .exe installer and portable version"
else
    echo "Detected Linux - Creating Linux packages..."
    npm run package -- --linux
    echo ""
    echo "✅ Linux packages created in dist/"
    echo "   - Look for .AppImage and .deb files"
fi

echo ""
echo "=========================================="
echo "Packaging complete!"
echo "=========================================="
echo ""
echo "Packages are in: electron/dist/"
echo ""
echo "IMPORTANT: Testers will need:"
echo "  1. Python 3.8+ installed"
echo "  2. audish package installed (pip install -e . from project root)"
echo "  3. Excel files ready for testing"
echo ""



