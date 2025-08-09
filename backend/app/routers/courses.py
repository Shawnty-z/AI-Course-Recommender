from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
import json
import logging

from ..models import (
    Course, CourseResponse, CourseSearchRequest, CourseFilters,
    InteractionCreate, InteractionResponse
)
from ..database import execute_query
from ..routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Dict[str, Any])
async def get_courses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    difficulty: Optional[str] = Query(None),
    topics: Optional[str] = Query(None)  # Comma-separated topics
):
    """Get all courses with optional filtering and pagination metadata"""
    try:
        # Build base query for counting
        count_query = "SELECT COUNT(*) FROM courses"
        query = "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses"
        params = []
        conditions = []
        
        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)
            
        if topics:
            topic_list = [topic.strip() for topic in topics.split(",")]
            for topic in topic_list:
                conditions.append("topics LIKE ?")
                params.append(f"%{topic}%")
        
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            count_query += where_clause
            query += where_clause
            
        # Get total count
        total_count = execute_query(count_query, tuple(params), fetch_one=True)[0]
        
        # Get paginated results
        query += f" LIMIT {limit} OFFSET {offset}"
        courses = execute_query(query, tuple(params))
        
        course_list = []
        for course in courses:
            topics_list = json.loads(course[3]) if course[3] else []
            course_list.append(CourseResponse(
                id=course[0],
                title=course[1],
                description=course[2],
                topics=topics_list,
                difficulty=course[4],
                duration=course[5],
                format=course[6],
                rating=course[7]
            ))
        
        return {
            "courses": course_list,
            "pagination": {
                "total": total_count,
                "page": (offset // limit) + 1,
                "limit": limit,
                "offset": offset,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch courses"
        )

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str):
    """Get a specific course by ID"""
    try:
        query = "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses WHERE id = ?"
        course = execute_query(query, (course_id,), fetch_one=True)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        topics_list = json.loads(course[3]) if course[3] else []
        
        return CourseResponse(
            id=course[0],
            title=course[1],
            description=course[2],
            topics=topics_list,
            difficulty=course[4],
            duration=course[5],
            format=course[6],
            rating=course[7]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course"
        )

@router.post("/search", response_model=List[CourseResponse])
async def search_courses(search_request: CourseSearchRequest):
    """Search courses with text query and filters"""
    try:
        query = """
            SELECT id, title, description, topics, difficulty, duration, format, rating 
            FROM courses 
            WHERE title LIKE ? OR description LIKE ?
        """
        params = [f"%{search_request.query}%", f"%{search_request.query}%"]
        conditions = []
        
        if search_request.filters:
            if search_request.filters.topics:
                for topic in search_request.filters.topics:
                    conditions.append("topics LIKE ?")
                    params.append(f"%{topic}%")
            
            if search_request.filters.difficulty:
                conditions.append("difficulty = ?")
                params.append(search_request.filters.difficulty)
                
            if search_request.filters.format:
                conditions.append("format = ?")
                params.append(search_request.filters.format)
                
            if search_request.filters.min_rating:
                conditions.append("rating >= ?")
                params.append(search_request.filters.min_rating)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        query += f" LIMIT {search_request.limit}"
        
        courses = execute_query(query, tuple(params))
        
        course_list = []
        for course in courses:
            topics_list = json.loads(course[3]) if course[3] else []
            course_list.append(CourseResponse(
                id=course[0],
                title=course[1],
                description=course[2],
                topics=topics_list,
                difficulty=course[4],
                duration=course[5],
                format=course[6],
                rating=course[7],
                similarity_score=0.8  # Placeholder for text similarity
            ))
        
        return course_list
        
    except Exception as e:
        logger.error(f"Error searching courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search courses"
        )

@router.post("/{course_id}/interact", response_model=InteractionResponse)
async def log_interaction(
    course_id: str,
    interaction: InteractionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Log user interaction with a course"""
    try:
        query = """
            INSERT INTO course_interactions (user_id, course_id, interaction_type) 
            VALUES (?, ?, ?) 
            RETURNING id, user_id, course_id, interaction_type, created_at
        """
        result = execute_query(
            query, 
            (current_user["id"], course_id, interaction.interaction_type.value), 
            fetch_one=True
        )
        
        if result:
            return InteractionResponse(
                id=result[0],
                user_id=result[1],
                course_id=result[2],
                interaction_type=result[3],
                created_at=result[4]
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log interaction"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log interaction"
        )

@router.get("/{course_id}/interactions", response_model=List[InteractionResponse])
async def get_course_interactions(
    course_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user's interactions with a specific course"""
    try:
        query = """
            SELECT id, user_id, course_id, interaction_type, created_at 
            FROM course_interactions 
            WHERE user_id = ? AND course_id = ?
            ORDER BY created_at DESC
        """
        interactions = execute_query(query, (current_user["id"], course_id))
        
        interaction_list = []
        for interaction in interactions:
            interaction_list.append(InteractionResponse(
                id=interaction[0],
                user_id=interaction[1],
                course_id=interaction[2],
                interaction_type=interaction[3],
                created_at=interaction[4]
            ))
        
        return interaction_list
        
    except Exception as e:
        logger.error(f"Error fetching interactions for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch interactions"
        ) 