from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import json
import logging
from datetime import datetime

from ..models import (
    FeedbackCreate, FeedbackResponse, UserPreferences, UserPreferencesUpdate
)
from ..database import execute_query
from ..routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user)
):
    """Submit feedback for a course"""
    try:
        query = """
            INSERT INTO user_feedback 
            (user_id, course_id, rating, feedback_text, learning_style, difficulty_preference, pace_preference) 
            VALUES (?, ?, ?, ?, ?, ?, ?) 
            RETURNING id, user_id, course_id, rating, feedback_text, learning_style, difficulty_preference, pace_preference, created_at
        """
        
        result = execute_query(
            query,
            (
                current_user["id"],
                feedback.course_id,
                feedback.rating,
                feedback.feedback_text,
                feedback.learning_style,
                feedback.difficulty_preference,
                feedback.pace_preference
            ),
            fetch_one=True
        )
        
        if result:
            # Update user preferences based on new feedback
            await update_user_preferences_from_feedback(current_user["id"], feedback)
            
            return FeedbackResponse(
                id=result[0],
                user_id=result[1],
                course_id=result[2],
                rating=result[3],
                feedback_text=result[4],
                learning_style=result[5],
                difficulty_preference=result[6],
                pace_preference=result[7],
                created_at=result[8]
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.get("/", response_model=List[FeedbackResponse])
async def get_user_feedback(current_user: dict = Depends(get_current_user)):
    """Get all feedback from the current user"""
    try:
        query = """
            SELECT id, user_id, course_id, rating, feedback_text, learning_style, 
                   difficulty_preference, pace_preference, created_at
            FROM user_feedback 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """
        feedback_list = execute_query(query, (current_user["id"],))
        
        result = []
        for feedback in feedback_list:
            result.append(FeedbackResponse(
                id=feedback[0],
                user_id=feedback[1],
                course_id=feedback[2],
                rating=feedback[3],
                feedback_text=feedback[4],
                learning_style=feedback[5],
                difficulty_preference=feedback[6],
                pace_preference=feedback[7],
                created_at=feedback[8]
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching user feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback"
        )

@router.get("/course/{course_id}", response_model=List[FeedbackResponse])
async def get_course_feedback(
    course_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user's feedback for a specific course"""
    try:
        query = """
            SELECT id, user_id, course_id, rating, feedback_text, learning_style, 
                   difficulty_preference, pace_preference, created_at
            FROM user_feedback 
            WHERE user_id = ? AND course_id = ? 
            ORDER BY created_at DESC
        """
        feedback_list = execute_query(query, (current_user["id"], course_id))
        
        result = []
        for feedback in feedback_list:
            result.append(FeedbackResponse(
                id=feedback[0],
                user_id=feedback[1],
                course_id=feedback[2],
                rating=feedback[3],
                feedback_text=feedback[4],
                learning_style=feedback[5],
                difficulty_preference=feedback[6],
                pace_preference=feedback[7],
                created_at=feedback[8]
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching course feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course feedback"
        )

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get user's current preferences"""
    try:
        query = """
            SELECT preferred_topics, difficulty_level, learning_style, time_commitment, excluded_topics
            FROM user_preferences 
            WHERE user_id = ?
        """
        preferences = execute_query(query, (current_user["id"],), fetch_one=True)
        
        if preferences:
            preferred_topics = json.loads(preferences[0]) if preferences[0] else []
            excluded_topics = json.loads(preferences[4]) if preferences[4] else []
            return UserPreferences(
                preferred_topics=preferred_topics,
                difficulty_level=preferences[1],
                learning_style=preferences[2],
                time_commitment=preferences[3],
                excluded_topics=excluded_topics
            )
        else:
            # Return default preferences for new users
            return UserPreferences(
                preferred_topics=[],
                difficulty_level=None,
                learning_style=None,
                time_commitment=None,
                excluded_topics=[]
            )
            
    except Exception as e:
        logger.error(f"Error fetching user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preferences"
        )

@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Get current preferences
        current_prefs = execute_query(
            "SELECT preferred_topics, difficulty_level, learning_style, time_commitment, excluded_topics FROM user_preferences WHERE user_id = ?",
            (current_user["id"],),
            fetch_one=True
        )
        
        # Merge with new preferences
        if current_prefs:
            current_topics = json.loads(current_prefs[0]) if current_prefs[0] else []
            current_excluded_topics = json.loads(current_prefs[4]) if current_prefs[4] else []
            new_topics = preferences.preferred_topics if preferences.preferred_topics is not None else current_topics
            new_excluded_topics = preferences.excluded_topics if preferences.excluded_topics is not None else current_excluded_topics
            new_difficulty = preferences.difficulty_level if preferences.difficulty_level is not None else current_prefs[1]
            new_learning_style = preferences.learning_style if preferences.learning_style is not None else current_prefs[2]
            new_time_commitment = preferences.time_commitment if preferences.time_commitment is not None else current_prefs[3]
            
            query = """
                UPDATE user_preferences 
                SET preferred_topics = ?, difficulty_level = ?, learning_style = ?, time_commitment = ?, excluded_topics = ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """
            execute_query(query, (json.dumps(new_topics), new_difficulty, new_learning_style, new_time_commitment, json.dumps(new_excluded_topics), current_user["id"]))
        else:
            # Insert new preferences
            query = """
                INSERT INTO user_preferences (user_id, preferred_topics, difficulty_level, learning_style, time_commitment, excluded_topics)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            new_topics = preferences.preferred_topics or []
            new_excluded_topics = preferences.excluded_topics or []
            execute_query(query, (
                current_user["id"],
                json.dumps(new_topics),
                preferences.difficulty_level,
                preferences.learning_style,
                preferences.time_commitment,
                json.dumps(new_excluded_topics)
            ))
            new_difficulty = preferences.difficulty_level
            new_learning_style = preferences.learning_style
            new_time_commitment = preferences.time_commitment
        
        return UserPreferences(
            preferred_topics=new_topics,
            difficulty_level=new_difficulty,
            learning_style=new_learning_style,
            time_commitment=new_time_commitment,
            excluded_topics=new_excluded_topics
        )
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

async def update_user_preferences_from_feedback(user_id: int, feedback: FeedbackCreate):
    """Update user preferences based on new feedback"""
    try:
        # Get course topics to update preferred topics
        course_query = "SELECT topics FROM courses WHERE id = ?"
        course = execute_query(course_query, (feedback.course_id,), fetch_one=True)
        
        if course and course[0]:
            course_topics = json.loads(course[0])
            
            # Get current preferences
            current_prefs = execute_query(
                "SELECT preferred_topics FROM user_preferences WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            # Update preferred topics based on rating
            if feedback.rating >= 4:  # Positive feedback
                if current_prefs and current_prefs[0]:
                    current_topics = json.loads(current_prefs[0])
                else:
                    current_topics = []
                
                # Add course topics to preferred topics
                for topic in course_topics:
                    if topic not in current_topics:
                        current_topics.append(topic)
                
                # Update or insert preferences
                if current_prefs:
                    execute_query(
                        "UPDATE user_preferences SET preferred_topics = ?, difficulty_level = ?, learning_style = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (json.dumps(current_topics), feedback.difficulty_preference, feedback.learning_style, user_id)
                    )
                else:
                    execute_query(
                        "INSERT INTO user_preferences (user_id, preferred_topics, difficulty_level, learning_style) VALUES (?, ?, ?, ?)",
                        (user_id, json.dumps(current_topics), feedback.difficulty_preference, feedback.learning_style)
                    )
                    
    except Exception as e:
        logger.error(f"Error updating preferences from feedback: {e}") 

@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete user's own feedback"""
    try:
        # First, check if the feedback exists and belongs to the current user
        check_query = """
            SELECT id, user_id, course_id FROM user_feedback 
            WHERE id = ? AND user_id = ?
        """
        feedback = execute_query(check_query, (feedback_id, current_user["id"]), fetch_one=True)
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found or you don't have permission to delete it"
            )
        
        # Delete the feedback
        delete_query = "DELETE FROM user_feedback WHERE id = ? AND user_id = ?"
        result = execute_query(delete_query, (feedback_id, current_user["id"]))
        
        logger.info(f"User {current_user['id']} deleted feedback {feedback_id} for course {feedback[2]}")
        
        return {"message": "Feedback deleted successfully", "deleted_id": feedback_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feedback"
        )

@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's own feedback"""
    try:
        # First, check if the feedback exists and belongs to the current user
        check_query = """
            SELECT id, user_id FROM user_feedback 
            WHERE id = ? AND user_id = ?
        """
        existing_feedback = execute_query(check_query, (feedback_id, current_user["id"]), fetch_one=True)
        
        if not existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found or you don't have permission to update it"
            )
        
        # Update the feedback
        update_query = """
            UPDATE user_feedback 
            SET rating = ?, feedback_text = ?, learning_style = ?, difficulty_preference = ?, pace_preference = ?
            WHERE id = ? AND user_id = ?
            RETURNING id, user_id, course_id, rating, feedback_text, learning_style, difficulty_preference, pace_preference, created_at
        """
        
        result = execute_query(
            update_query,
            (
                feedback.rating,
                feedback.feedback_text,
                feedback.learning_style,
                feedback.difficulty_preference,
                feedback.pace_preference,
                feedback_id,
                current_user["id"]
            ),
            fetch_one=True
        )
        
        if result:
            # Update user preferences based on updated feedback
            await update_user_preferences_from_feedback(current_user["id"], feedback)
            
            logger.info(f"User {current_user['id']} updated feedback {feedback_id}")
            
            return FeedbackResponse(
                id=result[0],
                user_id=result[1],
                course_id=result[2],
                rating=result[3],
                feedback_text=result[4],
                learning_style=result[5],
                difficulty_preference=result[6],
                pace_preference=result[7],
                created_at=result[8]
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback"
        ) 