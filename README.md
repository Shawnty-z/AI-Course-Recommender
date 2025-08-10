# AI Course Recommender App

A comprehensive AI-powered course recommendation system that learns from user feedback to provide personalized course suggestions. Built with React, FastAPI, Llama 3.2 1B, and enhanced with **Weaviate vector database** for semantic similarity search.

## Features

- **Personalized Recommendations**: AI-powered course suggestions based on user preferences and feedback
- * Vector Similarity Search**: Semantic course matching using AI embeddings 
- **Intelligent Learning**: System learns from user interactions and improves recommendations over time
- **Modern UI**: Clean, responsive React interface with Material-UI components
- **Real-time Feedback**: Immediate feedback processing and preference updates
- **Negative Preference Handling**: Users can specify topics they want to avoid
- **AI Reasoning Display**: Formatted explanations for why courses were recommended
- **Comprehensive Analytics**: User learning patterns and progress tracking

## Enhanced Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│   FastAPI Backend│────│   Llama 3.2 1B  │
│   - User Interface│    │   - API Endpoints│    │   - LLM Service │
│   - Feedback Forms│    │   - Business Logic│   │   - Via Ollama  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ├─────────────────┬─────────────────┬─────────────────┐
                                │                 │                 │                 │
                    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
                    │   Weaviate      │ │   SQLite        │ │   Embeddings    │ │ Enhanced Rec.   │
                    │   - Vector DB   │ │   - User Data   │ │   - Course Vec  │ │   - Hybrid AI   │
                    │   - Similarity  │ │   - Feedback    │ │   - User Prefs  │ │   - Multi-factor│
                    └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Enhanced Data Flow
1. **User Input** → Frontend collects feedback/queries (including negative preferences)
2. **API Processing** → FastAPI validates and routes requests
3. **Hybrid Retrieval** → Query vector DB for semantic similarity + fetch user history from SQLite
4. **Enhanced LLM Processing** → Llama 3.2 generates personalized recommendations using combined context
5. **Response Delivery** → Formatted recommendations with similarity scores and AI reasoning
6. **Memory Update** → New feedback stored in both databases for future learning

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLite**: Lightweight database for user data and feedback
- **Weaviate**: Vector database for semantic similarity search
- **SentenceTransformers**: AI embeddings for course content
- **Ollama + Llama 3.2 1B**: Local LLM for recommendation generation
- **Pydantic**: Data validation and serialization
- **Httpx**: Async HTTP client for LLM communication

### Frontend
- **React 18**: Modern React with hooks
- **Material-UI (MUI)**: Professional UI component library
- **React Router**: Client-side routing
- **React Query**: Server state management and caching
- **Axios**: HTTP client for API communication

## Prerequisites

- Python 3.8+
- Node.js 16+
- Ollama installed and running
- **Docker** (for Weaviate vector database)
- Git

## Quick Start

### 1. Install Ollama and Llama 3.2 1B

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai

# Pull Llama 3.2 1B model
ollama pull llama3.2:1b

# Start Ollama service
ollama serve
```

### 2. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies (including vector DB support)
pip install -r requirements.txt

# Initialize database with sample data
python sample_data.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Setup Frontend

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install Node dependencies
npm install

# Start React development server
npm start
```

### 4. Setup Vector Database (Enhanced AI Features)

```bash
# Option 1: Full vector database setup with Docker
./setup_vector_db.sh

# Option 2: Manual setup
docker-compose up -d weaviate
cd backend && python migrate_to_weaviate.py
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Weaviate Console**: http://localhost:8080/v1/schema (when running)

## Demo Access

Use the following credentials to try the application:
- **Username**: `demo_user`
- **Password**: Not required (demo mode)

The demo user comes with sample preferences and feedback data to showcase the recommendation system.

## AI Features

### Vector Similarity Search
- **Semantic Matching**: Finds courses based on meaning, not just keywords
- **AI Embeddings**: Uses SentenceTransformers to understand course content
- **Context-Aware**: Considers user preferences and learning history
- **Negative Filtering**: Excludes courses with topics users want to avoid

### Hybrid Recommendation Engine
- **Multi-Factor Scoring**: Combines vector similarity, user preferences, ratings, and learning style
- **Real-Time Learning**: Updates recommendations based on new user feedback
- **Negative Preference Handling**: Filters out courses with disliked topics
- **Collaborative Filtering**: Finds users with similar preferences (when Weaviate is running)

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Recommendations
- `GET /api/recommendations/{user_id}` - Get personalized recommendations with vector similarity
- `POST /api/recommendations/{user_id}` - Get recommendations with query (semantic search)
- `POST /api/recommendations/{user_id}/semantic-search` - Direct semantic search
- `POST /api/recommendations/{user_id}/similar` - Vector-based similar courses

### Vector Database Management
- `GET /api/admin/vector-db/health` - Check vector database status
- `POST /api/admin/vector-db/reindex` - Rebuild vector database

### Feedback
- `POST /api/feedback/` - Submit course feedback
- `GET /api/feedback/preferences` - Get user preferences
- `PUT /api/feedback/preferences` - Update user preferences

### Courses
- `GET /api/courses/` - List all courses
- `GET /api/courses/{course_id}` - Get specific course
- `POST /api/courses/search` - Search courses

## Sample Queries and Expected Results

### 1. Semantic Search
**Query**: "I want to learn machine learning with hands-on projects for beginners"

**Enhanced Output**: 
- **Vector Search**: Finds courses with similar semantic meaning
- **Similarity Scores**: Each recommendation includes AI-calculated similarity percentages
- **AI Reasoning**: Formatted explanations with course highlights and learning insights
- **Negative Filtering**: Excludes courses with topics you've specified to avoid

### 2. Personalized Vector Recommendations
**Context**: User liked Python (5/5), struggled with theory-heavy courses (2/5)

**Enhanced Output**:
- **Hybrid Matching**: Combines user history + vector similarity  
- **Smart Filtering**: Avoids theoretical courses, emphasizes practical ones
- **Negative Preference Learning**: Automatically excludes topics from poorly-rated courses
- **AI Explanation**: Formatted reasoning with personalized insights

## 📁 Enhanced Project Structure

```
AI-Course/
├── backend/
│   ├── app/
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic and LLM integration
│   │   │   ├── weaviate_service.py      # Vector database operations
│   │   │   ├── recommendation_engine.py  # Hybrid recommendations
│   │   │   └── llm_service.py           # LLM integration
│   │   ├── models.py         # Pydantic data models
│   │   ├── database.py       # SQLite connection and queries
│   │   ├── config.py         # Configuration settings
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt      # Python dependencies (includes vector DB)
│   ├── sample_data.py       # Database initialization script
│   └── migrate_to_weaviate.py  # Vector database migration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts (Auth, etc.)
│   │   ├── pages/          # Main page components
│   │   └── App.js          # Main React application
│   ├── package.json        # Node.js dependencies
│   └── public/            # Static assets
├── docker-compose.yml     # Weaviate database setup
├── setup_vector_db.sh     # Vector database setup script
├── data/                  # SQLite database files
└── README.md             # This file
```

## Current Implementation Status

### Completed
- [x] FastAPI backend with core endpoints
- [x] React frontend with authentication
- [x] SQLite database with sample data
- [x] LLM integration with Ollama
- [x] **Weaviate vector database integration**
- [x] **Semantic similarity search**
- [x] **Enhanced hybrid recommendation engine**
- [x] **AI embeddings for course content**
- [x] **Negative preference handling**
- [x] **AI reasoning display component**
- [x] User feedback system
- [x] Real-time preference updates

### 🔄 Available (when vector DB running)
- [x] **Vector similarity course search**
- [x] **Semantic query understanding**
- [x] **Enhanced personalization with embeddings**
- [x] **Negative preference filtering**
- [x] **Collaborative filtering capabilities**

## Testing

### Test Recommendations
```bash
# Start all services
./run_app.sh

# Test vector database integration
cd backend && python -c "from app.services.weaviate_service import weaviate_service; print(weaviate_service.health_check())"

# Run full system test
python test_system.py
```

### Test Semantic Search
```bash
# With vector database running
curl -X POST "http://localhost:8000/api/recommendations/1/semantic-search?query=machine%20learning%20for%20beginners&max_results=5"
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# API Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# Ollama Settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Database
DATABASE_URL=sqlite:///./data/app.db

# Vector Database (Weaviate)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
EMBEDDING_MODEL=all-MiniLM-L6-v2

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Running with Vector Database

### Option 1: Automated Setup
```bash
# One-command setup including vector database
./setup_vector_db.sh
```

### Option 2: Manual Setup
```bash
# Start Weaviate
docker-compose up -d weaviate

# Migrate data to vector database
cd backend && python migrate_to_weaviate.py

# Start backend with vector support
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## What's New with Vector Integration

### Enhanced User Experience
- **Smarter Search**: "Find courses like 'practical machine learning'" works semantically
- **Better Matching**: AI understands context beyond keywords
- **Negative Preferences**: Users can specify topics to avoid
- **AI Explanations**: Formatted reasoning for why courses were recommended
- **Improved Recommendations**: Higher relevance through semantic similarity

### Technical Improvements
- **Vector Embeddings**: All courses indexed with AI-generated embeddings
- **Hybrid Search**: Combines traditional filtering with semantic search
- **Scalable Architecture**: Ready for production with proper vector database

### Developer Benefits
- **New API Endpoints**: Semantic search and similarity endpoints
- **Enhanced Analytics**: Vector similarity scores and distance metrics
- **Future-Ready**: Foundation for advanced AI features like RAG

## Acknowledgments

- **Weaviate** for the powerful vector database
- **Sentence Transformers** for excellent embedding models
- **Ollama** for providing easy local LLM deployment
- **Meta** for the Llama 3.2 model
- **Material-UI** for the beautiful React components
- **FastAPI** for the excellent Python web framework