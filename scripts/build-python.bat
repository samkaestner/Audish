@echo off
REM =============================================================================
REM Build Script (Windows): Bundle Python + audish into standalone executable
REM =============================================================================
REM
REM This script uses PyInstaller to create a standalone executable that bundles:
REM - Python interpreter
REM - All Python dependencies (click, openpyxl, pyyaml, python-dateutil)
REM - The audish package
REM
REM Usage:
REM   scripts\build-python.bat [--clean]
REM
REM Output:
REM   dist\audish.exe
REM
REM =============================================================================

setlocal enabledelayedexpansion

echo === Building Python Executable (Windows) ===

REM Get project root (parent of scripts directory)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo Project root: %PROJECT_ROOT%

REM Check for --clean flag
if "%1"=="--clean" (
    echo Cleaning previous builds...
    if exist "dist\audish.exe" del /f "dist\audish.exe"
    if exist "build\audish" rmdir /s /q "build\audish"
)

REM Check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed.
    exit /b 1
)

REM Show Python version
python --version

REM Create virtual environment if it doesn't exist
set "VENV_DIR=%PROJECT_ROOT%\.venv-build"
if not exist "%VENV_DIR%" (
    echo Creating build virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install pyinstaller
pip install -e .

REM Verify audish is installed
python -c "import audish" >nul 2>&1
if errorlevel 1 (
    echo Error: audish package not properly installed
    exit /b 1
)

REM Build with PyInstaller
echo Running PyInstaller...
pyinstaller audish.spec --noconfirm

REM Verify the executable was created
if exist "dist\audish.exe" (
    echo Build successful!
    
    REM Test the executable
    echo Testing executable...
    dist\audish.exe --help
    if errorlevel 1 (
        echo Warning: Executable test failed
    ) else (
        echo Executable works!
    )
) else (
    echo Error: Build failed - executable not created
    exit /b 1
)

REM Deactivate virtual environment
call deactivate

echo.
echo === Build Complete ===
echo.
echo Next steps:
echo   1. Run 'npm run package' in the electron directory
echo   2. The packaged app will include the bundled Python executable

endlocal

