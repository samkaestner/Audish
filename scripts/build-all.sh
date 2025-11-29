#!/bin/bash
# =============================================================================
# Build Script: Complete build of Electron app with bundled Python
# =============================================================================
#
# This script:
# 1. Builds the Python executable with PyInstaller
# 2. Copies it to the electron resources directory
# 3. Builds the Electron app with electron-builder
#
# Usage:
#   ./scripts/build-all.sh [--mac|--win|--linux|--all]
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ELECTRON_DIR="$PROJECT_ROOT/electron"

# Parse arguments
PLATFORM="${1:---mac}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Audition Scheduler - Complete Build                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Platform: $PLATFORM"
echo ""

# Step 1: Build Python executable
echo -e "${YELLOW}━━━ Step 1/4: Building Python executable ━━━${NC}"
"$SCRIPT_DIR/build-python.sh" --clean

# Verify Python executable exists
PYTHON_EXE="$PROJECT_ROOT/dist/audish"
if [ ! -f "$PYTHON_EXE" ]; then
    echo -e "${RED}Error: Python executable not found at $PYTHON_EXE${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python executable ready${NC}"
echo ""

# Step 2: Copy Python executable to electron resources
echo -e "${YELLOW}━━━ Step 2/4: Copying Python executable to Electron resources ━━━${NC}"
RESOURCES_DIR="$ELECTRON_DIR/resources"
mkdir -p "$RESOURCES_DIR"

# Copy the executable
cp "$PYTHON_EXE" "$RESOURCES_DIR/audish-cli"
chmod +x "$RESOURCES_DIR/audish-cli"
echo -e "${GREEN}✓ Copied audish executable to electron/resources/${NC}"
echo ""

# Step 3: Build Electron renderer
echo -e "${YELLOW}━━━ Step 3/4: Building Electron app ━━━${NC}"
cd "$ELECTRON_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Electron dependencies..."
    npm install
fi

if [ ! -d "renderer/node_modules" ]; then
    echo "Installing renderer dependencies..."
    cd renderer && npm install && cd ..
fi

# Build the app
npm run build

echo -e "${GREEN}✓ Electron app built${NC}"
echo ""

# Step 4: Package Electron app
echo -e "${YELLOW}━━━ Step 4/4: Packaging Electron app ━━━${NC}"
case "$PLATFORM" in
    --mac)
        npm run package:mac
        ;;
    --win)
        npm run package:win
        ;;
    --linux)
        npm run package:linux
        ;;
    --all)
        npm run package:all
        ;;
    *)
        echo -e "${RED}Unknown platform: $PLATFORM${NC}"
        echo "Usage: $0 [--mac|--win|--linux|--all]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Build Complete!                                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Output files are in: $ELECTRON_DIR/dist/"
ls -la "$ELECTRON_DIR/dist/" 2>/dev/null || echo "(Directory listing not available)"
echo ""
echo -e "${BLUE}The app now includes a bundled Python runtime!${NC}"
echo "Users don't need to install Python separately."

