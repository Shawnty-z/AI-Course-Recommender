#!/bin/bash

# AI Course Recommender Setup Script
# This script sets up the entire application environment

set -e

echo "🎓 AI Course Recommender Setup"
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is not installed. Please install Node.js 16 or higher.${NC}"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}npm is not installed. Please install npm.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

# Setup Ollama
setup_ollama() {
    echo -e "${BLUE}Setting up Ollama...${NC}"
    
    if ! command -v ollama &> /dev/null; then
        echo -e "${YELLOW}Ollama not found. Please install Ollama first:${NC}"
        echo "  macOS: brew install ollama"
        echo "  Linux: curl https://ollama.ai/install.sh | sh"
        echo "  Windows: Download from https://ollama.ai"
        echo ""
        read -p "Press Enter after installing Ollama..."
    fi
    
    # Check if Ollama is running
    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "${YELLOW}Starting Ollama service...${NC}"
        ollama serve &
        sleep 3
    fi
    
    # Pull Llama 3.2 1B model
    echo -e "${BLUE}Downloading Llama 3.2 1B model (this may take a few minutes)...${NC}"
    ollama pull llama3.2:1b
    
    echo -e "${GREEN}✓ Ollama setup complete${NC}"
}

# Setup backend
setup_backend() {
    echo -e "${BLUE}Setting up backend...${NC}"
    
    cd backend
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Initialize database
    echo "Initializing database with sample data..."
    python sample_data.py
    
    cd ..
    echo -e "${GREEN}✓ Backend setup complete${NC}"
}

# Setup frontend
setup_frontend() {
    echo -e "${BLUE}Setting up frontend...${NC}"
    
    cd frontend
    
    # Install Node dependencies
    echo "Installing Node.js dependencies..."
    npm install
    
    cd ..
    echo -e "${GREEN}✓ Frontend setup complete${NC}"
}

# Create environment file
create_env() {
    echo -e "${BLUE}Creating environment configuration...${NC}"
    
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOL
# AI Course Recommender Configuration
DEBUG=True
SECRET_KEY=demo-secret-key-change-in-production
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
DATABASE_URL=sqlite:///./data/app.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOL
        echo -e "${GREEN}✓ Environment file created${NC}"
    else
        echo -e "${YELLOW}Environment file already exists${NC}"
    fi
}

# Main setup function
main() {
    echo "This script will set up the AI Course Recommender application."
    echo "It will install dependencies and initialize the database."
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
    
    check_requirements
    setup_ollama
    create_env
    setup_backend
    setup_frontend
    
    echo ""
    echo -e "${GREEN}🎉 Setup complete!${NC}"
    echo ""
    echo -e "${BLUE}To start the application:${NC}"
    echo "1. Backend: cd backend && uvicorn app.main:app --reload"
    echo "2. Frontend: cd frontend && npm start"
    echo ""
    echo -e "${BLUE}Then visit:${NC} http://localhost:3000"
    echo -e "${BLUE}Demo login:${NC} username 'demo_user'"
    echo ""
}

# Run main function
main "$@" 