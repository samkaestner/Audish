#!/bin/bash
# =============================================================================
# Build Script: Bundle Python + audish into standalone executable
# =============================================================================
#
# This script uses PyInstaller to create a standalone executable that bundles:
# - Python interpreter
# - All Python dependencies (click, openpyxl, pyyaml, python-dateutil)
# - The audish package
#
# The resulting executable can be called without needing Python installed.
#
# Usage:
#   ./scripts/build-python.sh [--clean]
#
# Output:
#   dist/audish (macOS/Linux) or dist/audish.exe (Windows)
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${GREEN}=== Building Python Executable ===${NC}"
echo "Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Check for --clean flag
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}Cleaning previous builds...${NC}"
    rm -rf dist/audish dist/audish.exe build/audish
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/.venv-build"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating build virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install pyinstaller
pip install -e .

# Verify audish is installed
if ! python -c "import audish" 2>/dev/null; then
    echo -e "${RED}Error: audish package not properly installed${NC}"
    exit 1
fi

# Build with PyInstaller
echo -e "${YELLOW}Running PyInstaller...${NC}"
pyinstaller audish.spec --noconfirm

# Verify the executable was created
if [ -f "dist/audish" ] || [ -f "dist/audish.exe" ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    # Show file size
    if [ -f "dist/audish" ]; then
        SIZE=$(du -h dist/audish | cut -f1)
        echo "  Executable: dist/audish ($SIZE)"
        
        # Test the executable
        echo -e "${YELLOW}Testing executable...${NC}"
        ./dist/audish --help && echo -e "${GREEN}✓ Executable works!${NC}"
    else
        SIZE=$(du -h dist/audish.exe | cut -f1)
        echo "  Executable: dist/audish.exe ($SIZE)"
    fi
else
    echo -e "${RED}Error: Build failed - executable not created${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate

echo -e "${GREEN}=== Build Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Run 'npm run package' in the electron directory"
echo "  2. The packaged app will include the bundled Python executable"

