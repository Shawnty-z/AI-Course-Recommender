#!/bin/bash

# AI Course Recommender Run Script
# Starts both backend and frontend services

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎓 Starting AI Course Recommender${NC}"
echo "=================================="

# Function to cleanup background processes
cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit
}

# Set trap for cleanup on script exit
trap cleanup INT TERM EXIT

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${BLUE}Starting Ollama service...${NC}"
    ollama serve &
    sleep 3
fi

# Start backend
echo -e "${BLUE}Starting FastAPI backend...${NC}"
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo -e "${BLUE}Starting React frontend...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✅ Application started successfully!${NC}"
echo ""
echo -e "${BLUE}🌐 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}🚀 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🤖 Demo Login:${NC} username 'demo_user'"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for background processes
wait 