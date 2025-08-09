#!/bin/bash

# Enhanced AI Course Recommender - System Shutdown Script

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Enhanced AI Course Recommender System${NC}"
echo "=================================================="

echo -e "${YELLOW}Stopping Frontend...${NC}"
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo -e "${YELLOW}Stopping Backend API...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null || true

echo -e "${YELLOW}Stopping Weaviate Vector Database...${NC}"
docker stop weaviate-demo 2>/dev/null || true
docker rm weaviate-demo 2>/dev/null || true

echo -e "${YELLOW}Cleaning up processes...${NC}"
sleep 3

echo -e "${GREEN}✅ All services stopped successfully!${NC}"
echo ""
echo -e "${BLUE}To restart the system, run: ./start_system.sh${NC}" 