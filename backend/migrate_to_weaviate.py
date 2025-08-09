#!/usr/bin/env python3
"""
Migration script to populate Weaviate vector database with existing course data
"""

import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.weaviate_service import weaviate_service
from app.database import execute_query
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_courses_to_weaviate():
    """Migrate all courses from SQLite to Weaviate"""
    try:
        # First, create the Weaviate schema
        logger.info("Creating Weaviate schema...")
        if not weaviate_service.create_schema():
            logger.error("Failed to create Weaviate schema")
            return False
        
        # Get all courses from SQLite
        logger.info("Fetching courses from SQLite...")
        courses = execute_query(
            "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses"
        )
        
        if not courses:
            logger.warning("No courses found in SQLite database")
            return False
        
        logger.info(f"Found {len(courses)} courses to migrate")
        
        # Migrate each course
        successful_migrations = 0
        failed_migrations = 0
        
        for course in courses:
            try:
                # Parse topics JSON
                topics = json.loads(course[3]) if course[3] else []
                
                # Prepare course data
                course_data = {
                    'id': course[0],
                    'title': course[1],
                    'description': course[2],
                    'topics': topics,
                    'difficulty': course[4],
                    'duration': course[5],
                    'format': course[6],
                    'rating': course[7]
                }
                
                # Add to Weaviate
                if weaviate_service.add_course(course_data):
                    successful_migrations += 1
                    logger.info(f"✓ Migrated course: {course[1]}")
                else:
                    failed_migrations += 1
                    logger.error(f"✗ Failed to migrate course: {course[1]}")
                    
            except Exception as e:
                failed_migrations += 1
                logger.error(f"✗ Error migrating course {course[0]}: {e}")
        
        logger.info(f"Migration complete: {successful_migrations} successful, {failed_migrations} failed")
        return successful_migrations > 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def migrate_user_preferences():
    """Migrate user preferences to Weaviate"""
    try:
        logger.info("Migrating user preferences...")
        
        # Get user preferences and feedback to build preference profiles
        users_query = """
            SELECT DISTINCT u.id, u.username,
                   up.preferred_topics, up.difficulty_level, up.learning_style,
                   GROUP_CONCAT(uf.course_id) as rated_courses,
                   AVG(uf.rating) as avg_rating
            FROM users u
            LEFT JOIN user_preferences up ON u.id = up.user_id
            LEFT JOIN user_feedback uf ON u.id = uf.user_id
            GROUP BY u.id
        """
        
        users = execute_query(users_query)
        
        for user in users:
            try:
                user_id = str(user[0])
                preferred_topics = json.loads(user[2]) if user[2] else []
                
                # Get topics from highly rated courses
                topics_liked = preferred_topics.copy()
                
                # Get topics from courses the user rated highly
                if user[5]:  # rated_courses
                    course_ids = user[5].split(',')
                    for course_id in course_ids:
                        course = execute_query(
                            "SELECT topics FROM courses WHERE id = ?", 
                            (course_id.strip(),), 
                            fetch_one=True
                        )
                        if course and course[0]:
                            course_topics = json.loads(course[0])
                            topics_liked.extend(course_topics)
                
                # Remove duplicates
                topics_liked = list(set(topics_liked))
                
                # Create preference text for embedding
                feedback_summary = f"User prefers {user[3] or 'various'} difficulty level courses"
                if user[4]:  # learning_style
                    feedback_summary += f" with {user[4]} learning style"
                if user[6]:  # avg_rating
                    feedback_summary += f" and typically rates courses {user[6]:.1f}/5"
                
                preference_data = {
                    'topics_liked': topics_liked,
                    'topics_disliked': [],  # Could be inferred from low-rated courses
                    'learning_style': user[4] or '',
                    'difficulty_level': user[3] or '',
                    'feedback_summary': feedback_summary,
                    'timestamp': '2024-01-01T00:00:00Z'
                }
                
                if weaviate_service.add_user_preference(user_id, preference_data):
                    logger.info(f"✓ Migrated preferences for user: {user[1]}")
                else:
                    logger.error(f"✗ Failed to migrate preferences for user: {user[1]}")
                    
            except Exception as e:
                logger.error(f"✗ Error migrating preferences for user {user[0]}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"User preference migration failed: {e}")
        return False

def test_vector_search():
    """Test vector search functionality"""
    try:
        logger.info("Testing vector search...")
        
        # Test searches
        test_queries = [
            "I want to learn Python programming for beginners",
            "Advanced machine learning and artificial intelligence",
            "Web development with modern frameworks",
            "Data visualization and analytics"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            results = weaviate_service.search_similar_courses(query, limit=3)
            
            if results:
                logger.info(f"Found {len(results)} similar courses:")
                for i, course in enumerate(results, 1):
                    logger.info(f"  {i}. {course['title']} (similarity: {course['similarity_score']:.3f})")
            else:
                logger.warning(f"No results found for query: {query}")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector search test failed: {e}")
        return False

def check_weaviate_health():
    """Check Weaviate connection and health"""
    try:
        health = weaviate_service.health_check()
        logger.info(f"Weaviate health check: {health}")
        
        if health['status'] == 'connected':
            logger.info("✓ Weaviate is connected and ready")
            return True
        else:
            logger.error("✗ Weaviate is not ready")
            return False
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def main():
    """Run the migration"""
    logger.info("Starting Weaviate migration...")
    
    # Check if Weaviate is available
    if not check_weaviate_health():
        logger.error("Weaviate is not available. Please start Weaviate server first.")
        logger.info("To start Weaviate locally with Docker:")
        logger.info("docker run -p 8080:8080 -p 50051:50051 weaviate/weaviate:1.26.1")
        return 1
    
    # Migrate courses
    if not migrate_courses_to_weaviate():
        logger.error("Course migration failed")
        return 1
    
    # Migrate user preferences
    if not migrate_user_preferences():
        logger.error("User preference migration failed")
        return 1
    
    # Test vector search
    if not test_vector_search():
        logger.error("Vector search test failed")
        return 1
    
    logger.info("Migration completed successfully.")
    logger.info("Vector database is ready for recommendations.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 