from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import json
import logging

from ..models import RecommendationRequest, RecommendationResponse, CourseResponse
from ..database import execute_query
from ..routers.auth import get_current_user
from ..services.llm_service import LLMService
from ..services.recommendation_engine import recommendation_engine
from ..services.weaviate_service import weaviate_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()

@router.post("/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get personalized course recommendations (vector + content filtering)"""
    try:
        # Verify user access
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get user context
        user_context = await get_user_context(user_id)
        
        # Generate recommendations
        recommendations = await recommendation_engine.get_personalized_recommendations(
            user_id=user_id,
            query=request.query,
            user_context=user_context,
            max_results=request.max_results
        )
        
        # Generate reasoning if requested
        reasoning = None
        if request.include_reasoning and recommendations:
            reasoning = await llm_service.generate_recommendation_reasoning(
                recommendations=recommendations,
                user_context=user_context,
                query=request.query
            )
        
        return RecommendationResponse(
            courses=recommendations,
            reasoning=reasoning,
            user_context=user_context,
            query_processed=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )

@router.get("/{user_id}", response_model=RecommendationResponse)
async def get_default_recommendations(
    user_id: int,
    max_results: int = 10,
    force_refresh: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get default recommendations"""
    try:
        # Verify user access
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        request = RecommendationRequest(
            query=None,
            max_results=max_results,
            include_reasoning=True
        )
        
        user_context = await get_user_context(user_id)
        recommendations = await recommendation_engine.get_personalized_recommendations(
            user_id=user_id,
            query=None,
            user_context=user_context,
            max_results=max_results,
            force_refresh=force_refresh
        )
        
        reasoning = None
        if recommendations:
            reasoning = await llm_service.generate_recommendation_reasoning(
                recommendations=recommendations,
                user_context=user_context,
                query=None
            )
        
        return RecommendationResponse(
            courses=recommendations,
            reasoning=reasoning,
            user_context=user_context,
            query_processed=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating default recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )

@router.post("/{user_id}/similar", response_model=List[CourseResponse])
async def get_similar_courses(
    user_id: int,
    course_id: str,
    max_results: int = 5,
    use_vector_search: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get courses similar to a specific course using vector similarity"""
    try:
        # Verify user access
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if use_vector_search:
            similar_courses = await recommendation_engine.get_similar_courses_vector(
                course_id=course_id,
                max_results=max_results
            )
        else:
            similar_courses = []
        
        return similar_courses
        
    except Exception as e:
        logger.error(f"Error finding similar courses for {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar courses"
        )

@router.post("/{user_id}/semantic-search", response_model=List[CourseResponse])
async def semantic_course_search(
    user_id: int,
    query: str,
    max_results: int = 10,
    min_similarity: float = 0.25,
    exclude_topics: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Perform semantic search for courses using vector similarity with negative filtering"""
    try:
        # Verify user access
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        exclude_list: List[str] = []
        if exclude_topics:
            exclude_list = [topic.strip() for topic in exclude_topics.split(",")]
        
        search_results = weaviate_service.search_similar_courses(
            query_text=query,
            limit=max_results,
            min_certainty=min_similarity,
            exclude_topics=exclude_list
        )
        
        courses = []
        for result in search_results:
            course_response = CourseResponse(
                id=result['id'],
                title=result['title'],
                description=result['description'],
                topics=result['topics'],
                difficulty=result['difficulty'],
                duration=result['duration'],
                format=result['format'],
                rating=result['rating'],
                similarity_score=result['similarity_score']
            )
            courses.append(course_response)
        
        logger.info(f"Semantic search returned {len(courses)} courses for query: '{query}'" + 
                   (f" (excluding: {exclude_topics})" if exclude_topics else ""))
        
        return courses
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform semantic search"
        )

@router.get("/{user_id}/history")
async def get_recommendation_history(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get user's recommendation history and feedback patterns"""
    try:
        # Verify user access
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get user feedback summary
        feedback_query = """
            SELECT 
                COUNT(*) as total_feedback,
                AVG(rating) as avg_rating,
                learning_style,
                difficulty_preference,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback
            FROM user_feedback 
            WHERE user_id = ?
            GROUP BY learning_style, difficulty_preference
            ORDER BY COUNT(*) DESC
        """
        feedback_stats = execute_query(feedback_query, (user_id,))
        
        # Get interaction summary
        interaction_query = """
            SELECT 
                interaction_type,
                COUNT(*) as count
            FROM course_interactions 
            WHERE user_id = ?
            GROUP BY interaction_type
        """
        interaction_stats = execute_query(interaction_query, (user_id,))
        
        # Get preferred topics from recent feedback
        topics_query = """
            SELECT c.topics, uf.rating
            FROM user_feedback uf
            JOIN courses c ON uf.course_id = c.id
            WHERE uf.user_id = ? AND uf.rating >= 4
            ORDER BY uf.created_at DESC
            LIMIT 10
        """
        recent_preferences = execute_query(topics_query, (user_id,))
        
        # Aggregate preferred topics
        topic_counts: Dict[str, int] = {}
        for pref in recent_preferences:
            if pref[0]:
                topics = json.loads(pref[0])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            "feedback_summary": [dict(stat) for stat in feedback_stats],
            "interaction_summary": [dict(stat) for stat in interaction_stats],
            "preferred_topics": sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "total_interactions": sum([stat[1] for stat in interaction_stats]),
            "vector_search_enabled": weaviate_service.client is not None
        }
        
    except Exception as e:
        logger.error(f"Error fetching recommendation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recommendation history"
        )

# Vector Database Management Endpoints

@router.get("/admin/vector-db/health")
async def vector_db_health():
    """Check vector database health (admin endpoint)"""
    try:
        health_status = weaviate_service.health_check()
        return {
            "weaviate": health_status,
            "recommendation_engine": "vector" if health_status['status'] == 'connected' else "basic"
        }
    except Exception as e:
        logger.error(f"Error checking vector DB health: {e}")
        return {
            "weaviate": {"status": "error", "message": str(e)},
            "recommendation_engine": "basic"
        }

@router.post("/admin/vector-db/reindex")
async def reindex_vector_database():
    """Reindex all courses in vector database (admin endpoint)"""
    try:
        logger.info("Starting vector database reindexing...")
        courses = execute_query(
            "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses"
        )
        weaviate_service.create_schema()
        successful = 0
        failed = 0
        for course in courses:
            course_data = {
                'id': course[0],
                'title': course[1],
                'description': course[2],
                'topics': json.loads(course[3]) if course[3] else [],
                'difficulty': course[4],
                'duration': course[5],
                'format': course[6],
                'rating': course[7]
            }
            if weaviate_service.add_course(course_data):
                successful += 1
            else:
                failed += 1
        return {
            "message": "Vector database reindexing completed",
            "successful": successful,
            "failed": failed,
            "total": len(courses)
        }
    except Exception as e:
        logger.error(f"Error reindexing vector database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex vector database: {str(e)}"
        )

async def get_user_context(user_id: int) -> Dict[str, Any]:
    """Get comprehensive user context for recommendations"""
    try:
        prefs_query = """
            SELECT preferred_topics, difficulty_level, learning_style, time_commitment
            FROM user_preferences 
            WHERE user_id = ?
        """
        preferences = execute_query(prefs_query, (user_id,), fetch_one=True)
        
        feedback_query = """
            SELECT course_id, rating, feedback_text, learning_style, difficulty_preference
            FROM user_feedback 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """
        recent_feedback = execute_query(feedback_query, (user_id,))
        
        interaction_query = """
            SELECT course_id, interaction_type, created_at
            FROM course_interactions 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        """
        recent_interactions = execute_query(interaction_query, (user_id,))
        
        context = {
            "user_id": user_id,
            "preferences": {
                "topics": json.loads(preferences[0]) if preferences and preferences[0] else [],
                "difficulty": preferences[1] if preferences else None,
                "learning_style": preferences[2] if preferences else None,
                "time_commitment": preferences[3] if preferences else None
            } if preferences else {"topics": [], "difficulty": None, "learning_style": None, "time_commitment": None},
            "recent_feedback": [
                {
                    "course_id": f[0],
                    "rating": f[1],
                    "feedback_text": f[2],
                    "learning_style": f[3],
                    "difficulty_preference": f[4]
                }
                for f in recent_feedback
            ],
            "recent_interactions": [
                {
                    "course_id": i[0],
                    "interaction_type": i[1],
                    "created_at": str(i[2])
                }
                for i in recent_interactions
            ],
            "vector_search_available": weaviate_service.client is not None
        }
        return context
    except Exception as e:
        logger.error(f"Error building user context: {e}")
        return {
            "user_id": user_id,
            "preferences": {"topics": [], "difficulty": None, "learning_style": None, "time_commitment": None},
            "recent_feedback": [],
            "recent_interactions": [],
            "vector_search_available": False
        } 