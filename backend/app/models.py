from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# User Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    created_at: datetime

# Course Models
class Course(BaseModel):
    id: str
    title: str
    description: str
    topics: List[str]
    difficulty: str
    duration: str
    format: str
    rating: float = 0.0

class CourseResponse(BaseModel):
    id: str
    title: str
    description: str
    topics: List[str]
    difficulty: str
    duration: str
    format: str
    rating: float
    similarity_score: Optional[float] = None

# Feedback Models
class FeedbackCreate(BaseModel):
    course_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    learning_style: Optional[str] = None
    difficulty_preference: Optional[str] = None
    pace_preference: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    course_id: str
    rating: int
    feedback_text: Optional[str]
    learning_style: Optional[str]
    difficulty_preference: Optional[str]
    pace_preference: Optional[str]
    created_at: datetime

# Interaction Models
class InteractionType(str, Enum):
    VIEWED = "viewed"
    ENROLLED = "enrolled"
    COMPLETED = "completed"
    DROPPED = "dropped"

class InteractionCreate(BaseModel):
    course_id: str
    interaction_type: InteractionType

class InteractionResponse(BaseModel):
    id: int
    user_id: int
    course_id: str
    interaction_type: str
    created_at: datetime

# Recommendation Models
class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    max_results: Optional[int] = Field(10, ge=1, le=20)
    include_reasoning: bool = True

class RecommendationResponse(BaseModel):
    courses: List[CourseResponse]
    reasoning: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    query_processed: Optional[str] = None

# User Preferences Models
class UserPreferences(BaseModel):
    preferred_topics: List[str]
    excluded_topics: Optional[List[str]] = []  # Topics user doesn't want to learn
    difficulty_level: Optional[str] = None
    learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

class UserPreferencesUpdate(BaseModel):
    preferred_topics: Optional[List[str]] = None
    excluded_topics: Optional[List[str]] = None  # Topics user wants to exclude
    difficulty_level: Optional[str] = None
    learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

# Search and Filter Models
class CourseFilters(BaseModel):
    topics: Optional[List[str]] = None
    difficulty: Optional[str] = None
    format: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_duration: Optional[str] = None

class CourseSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: Optional[CourseFilters] = None
    limit: int = Field(10, ge=1, le=50)

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 