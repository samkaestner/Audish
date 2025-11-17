@echo off
echo ======================================
echo   Starting Audish Scheduling System
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed. Please install Node.js 18 or higher.
    pause
    exit /b 1
)

REM Install Python dependencies
if not exist "api\venv" (
    echo Creating Python virtual environment...
    python -m venv api\venv
)

echo Installing Python dependencies...
call api\venv\Scripts\activate.bat
pip install -q -r requirements.txt
pip install -q -r api\requirements.txt

REM Install Node.js dependencies
if not exist "web\node_modules" (
    echo Installing Node.js dependencies...
    cd web
    call npm install
    cd ..
)

REM Start backend API server
echo Starting backend API server on port 8000...
start "Audish Backend" cmd /k "cd api && ..\api\venv\Scripts\activate.bat && python main.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend development server
echo Starting frontend development server on port 3000...
start "Audish Frontend" cmd /k "cd web && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak >nul

REM Open browser
echo Opening browser...
start http://localhost:3000

echo.
echo ======================================
echo   Audish is now running!
echo ======================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo.
echo   Close the terminal windows to stop
echo ======================================
echo.
pause
