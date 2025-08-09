#!/bin/bash

# Enhanced AI Course Recommender - Complete System Startup
# This script starts all components with vector database integration

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Enhanced AI Course Recommender System${NC}"
echo "================================================================="

# Function to check if a port is in use
check_port() {
    nc -z localhost $1 2>/dev/null
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}❌ $service_name failed to start within $((max_attempts * 2)) seconds${NC}"
    return 1
}

echo -e "${BLUE}Step 1: Starting Weaviate Vector Database${NC}"
echo "================================================"

# Check if Weaviate is already running
if check_port 8080; then
    echo -e "${GREEN}✅ Weaviate is already running on port 8080${NC}"
else
    echo "🔄 Starting Weaviate container..."
    
    # Stop and remove existing container if it exists
    docker stop weaviate-demo 2>/dev/null || true
    docker rm weaviate-demo 2>/dev/null || true
    
    # Start Weaviate
    docker run -d -p 8080:8080 -p 50051:50051 --name weaviate-demo \
        cr.weaviate.io/semitechnologies/weaviate:1.32.0
    
    # Wait for Weaviate to be ready
    wait_for_service "http://localhost:8080/v1/.well-known/ready" "Weaviate"
fi

echo -e "${BLUE}Step 2: Migrating Data to Vector Database${NC}"
echo "=============================================="

cd backend
echo "🔄 Populating Weaviate with course data and creating embeddings..."
python migrate_to_weaviate.py

echo -e "${BLUE}Step 3: Starting Backend API${NC}"
echo "=============================="

# Check if backend is already running
if check_port 8000; then
    echo -e "${GREEN}✅ Backend API is already running on port 8000${NC}"
else
    echo "🔄 Starting FastAPI backend with enhanced AI features..."
    
    # Kill existing backend processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 2
    
    # Start backend in background
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    
    # Wait for backend to be ready
    wait_for_service "http://localhost:8000/health" "Backend API"
fi

cd ..

echo -e "${BLUE}Step 4: Starting Frontend${NC}"
echo "=========================="

# Check if frontend is already running
if check_port 3000; then
    echo -e "${GREEN}✅ Frontend is already running on port 3000${NC}"
else
    echo "🔄 Starting React frontend..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Kill existing frontend processes
    pkill -f "react-scripts start" 2>/dev/null || true
    sleep 2
    
    # Start frontend in background
    nohup npm start > ../logs/frontend.log 2>&1 &
    
    cd ..
    
    # Wait for frontend to be ready
    wait_for_service "http://localhost:3000" "Frontend"
fi

echo -e "${BLUE}Step 5: System Health Check${NC}"
echo "=============================="

echo "🔍 Verifying all services..."

# Create logs directory
mkdir -p logs

# Check Weaviate
if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
    echo -e "${GREEN}✅ Weaviate Vector Database: RUNNING${NC}"
    # Check vector database health
    curl -s http://localhost:8000/api/admin/vector-db/health 2>/dev/null | grep -q "connected" && \
        echo -e "${GREEN}✅ Vector Database Integration: ACTIVE${NC}" || \
        echo -e "${YELLOW}⚠️  Vector Database Integration: INITIALIZING${NC}"
else
    echo -e "${RED}❌ Weaviate Vector Database: FAILED${NC}"
fi

# Check Backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend API: RUNNING${NC}"
else
    echo -e "${RED}❌ Backend API: FAILED${NC}"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend React App: RUNNING${NC}"
else
    echo -e "${RED}❌ Frontend React App: FAILED${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Enhanced AI Course Recommender System Started!${NC}"
echo "============================================================="
echo ""
echo -e "${BLUE}🌟 Available Services:${NC}"
echo "🔹 Frontend (React):     http://localhost:3000"
echo "🔹 Backend API:          http://localhost:8000"
echo "🔹 API Documentation:    http://localhost:8000/docs"
echo "🔹 Weaviate Console:     http://localhost:8080/v1/schema"
echo ""
echo -e "${BLUE}🧠 Enhanced AI Features:${NC}"
echo "✨ Semantic course search using AI embeddings"
echo "✨ Vector similarity-based recommendations"
echo "✨ Hybrid AI algorithm (Vector + Collaborative filtering)"
echo "✨ Intelligent personalization with user context"
echo ""
echo -e "${BLUE}🎯 Demo Login:${NC}"
echo "Username: demo_user (no password required)"
echo ""
echo -e "${BLUE}📋 New API Endpoints:${NC}"
echo "• POST /api/recommendations/{user_id}/semantic-search"
echo "• POST /api/recommendations/{user_id}/similar"
echo "• GET  /api/admin/vector-db/health"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo "Backend logs: tail -f logs/backend.log"
echo "Frontend logs: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}To stop all services, run: ./stop_system.sh${NC}" 