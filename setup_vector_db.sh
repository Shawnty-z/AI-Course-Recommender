#!/bin/bash

# Vector Database Setup Script for AI Course Recommender
# Sets up Weaviate and migrates data to enable enhanced semantic search

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up Vector Database (Weaviate) Integration${NC}"
echo "=============================================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        echo "   macOS: Start Docker Desktop"
        echo "   Linux: sudo systemctl start docker"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to start Weaviate
start_weaviate() {
    echo -e "${BLUE}Starting Weaviate vector database...${NC}"
    
    if docker-compose ps | grep weaviate | grep -q Up; then
        echo -e "${YELLOW}Weaviate is already running${NC}"
    else
        docker-compose up -d weaviate
        echo -e "${BLUE}Waiting for Weaviate to be ready...${NC}"
        
        # Wait for Weaviate to be healthy
        for i in {1..30}; do
            if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
                echo -e "${GREEN}✓ Weaviate is ready!${NC}"
                return 0
            fi
            echo -n "."
            sleep 2
        done
        
        echo -e "${RED}❌ Weaviate failed to start within 60 seconds${NC}"
        exit 1
    fi
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${BLUE}Installing vector database dependencies...${NC}"
    cd backend
    
    # Install additional dependencies if not already installed
    pip install weaviate-client sentence-transformers numpy > /dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    cd ..
}

# Function to run migration
migrate_data() {
    echo -e "${BLUE}Migrating course data to vector database...${NC}"
    cd backend
    
    python migrate_to_weaviate.py
    migration_result=$?
    
    cd ..
    
    if [ $migration_result -eq 0 ]; then
        echo -e "${GREEN}✓ Data migration completed successfully${NC}"
    else
        echo -e "${RED}❌ Data migration failed${NC}"
        exit 1
    fi
}

# Function to test vector search
test_vector_search() {
    echo -e "${BLUE}Testing vector search functionality...${NC}"
    
    # Test basic connection
    if curl -s http://localhost:8080/v1/schema > /dev/null; then
        echo -e "${GREEN}✓ Weaviate API accessible${NC}"
    else
        echo -e "${RED}❌ Cannot access Weaviate API${NC}"
        return 1
    fi
    
    # Test if classes exist
    schema_response=$(curl -s http://localhost:8080/v1/schema)
    if echo "$schema_response" | grep -q "Course"; then
        echo -e "${GREEN}✓ Course schema created${NC}"
    else
        echo -e "${YELLOW}⚠ Course schema not found${NC}"
    fi
    
    if echo "$schema_response" | grep -q "UserPreference"; then
        echo -e "${GREEN}✓ UserPreference schema created${NC}"
    else
        echo -e "${YELLOW}⚠ UserPreference schema not found${NC}"
    fi
}

# Function to update backend configuration
update_backend_config() {
    echo -e "${BLUE}Updating backend configuration...${NC}"
    
    # Check if .env file exists, create if not
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOL
# AI Course Recommender Configuration
DEBUG=True
SECRET_KEY=demo-secret-key-change-in-production
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
DATABASE_URL=sqlite:///./data/app.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
EMBEDDING_MODEL=all-MiniLM-L6-v2
EOL
        echo -e "${GREEN}✓ Created .env file with Weaviate configuration${NC}"
    else
        # Update existing .env file
        if grep -q "WEAVIATE_URL" backend/.env; then
            echo -e "${YELLOW}Weaviate configuration already exists in .env${NC}"
        else
            echo "" >> backend/.env
            echo "# Weaviate Configuration" >> backend/.env
            echo "WEAVIATE_URL=http://localhost:8080" >> backend/.env
            echo "WEAVIATE_API_KEY=" >> backend/.env
            echo "EMBEDDING_MODEL=all-MiniLM-L6-v2" >> backend/.env
            echo -e "${GREEN}✓ Added Weaviate configuration to .env${NC}"
        fi
    fi
}

# Function to restart backend
restart_backend() {
    echo -e "${BLUE}Restarting backend to load vector database...${NC}"
    
    # Kill existing backend process if running
    pkill -f "uvicorn app.main:app" || true
    sleep 2
    
    # Start backend in background
    cd backend
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
    cd ..
    
    # Wait for backend to start
    echo -e "${BLUE}Waiting for backend to start...${NC}"
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✓ Backend restarted with vector database integration${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
}

# Function to show status and usage
show_status() {
    echo ""
    echo -e "${GREEN}🎉 Vector Database Integration Complete!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}Services Status:${NC}"
    echo "🔹 Weaviate: http://localhost:8080"
    echo "🔹 Backend API: http://localhost:8000"
    echo "🔹 Frontend: http://localhost:3000"
    echo ""
    echo -e "${BLUE}New Features Available:${NC}"
    echo "✨ Semantic course search using AI embeddings"
    echo "✨ Enhanced personalized recommendations"
    echo "✨ Vector similarity-based course matching"
    echo "✨ Improved content discovery"
    echo ""
    echo -e "${BLUE}Test the Enhancement:${NC}"
    echo "1. Visit the frontend: http://localhost:3000"
    echo "2. Login with 'demo_user'"
    echo "3. Notice improved recommendations with better matching"
    echo "4. Try the new semantic search capabilities"
    echo ""
    echo -e "${BLUE}API Endpoints:${NC}"
    echo "• GET /api/recommendations/{user_id}/semantic-search"
    echo "• GET /api/admin/vector-db/health"
    echo "• POST /api/admin/vector-db/reindex"
    echo ""
    echo -e "${BLUE}To stop services:${NC}"
    echo "docker-compose down"
}

# Main execution
main() {
    echo "This script will set up vector database integration for enhanced AI recommendations."
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_docker
    update_backend_config
    install_dependencies
    start_weaviate
    migrate_data
    test_vector_search
    restart_backend
    show_status
}

# Run main function
main "$@" 