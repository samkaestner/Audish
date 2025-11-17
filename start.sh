#!/bin/bash

echo "======================================"
echo "  Starting Audish Scheduling System  "
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Install Python dependencies if needed
if [ ! -d "api/venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv api/venv
fi

echo -e "${YELLOW}Installing Python dependencies...${NC}"
source api/venv/bin/activate
pip install -q -r requirements.txt
pip install -q -r api/requirements.txt

# Install Node.js dependencies if needed
if [ ! -d "web/node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    cd web && npm install && cd ..
fi

# Start the backend API server
echo -e "${GREEN}Starting backend API server on port 8000...${NC}"
source api/venv/bin/activate
cd api && python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start the frontend development server
echo -e "${GREEN}Starting frontend development server on port 3000...${NC}"
cd web && npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

# Open browser
echo -e "${GREEN}Opening browser...${NC}"
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

echo ""
echo "======================================"
echo "  Audish is now running!             "
echo "======================================"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "======================================"
echo ""

# Wait for user to stop
wait $BACKEND_PID $FRONTEND_PID
