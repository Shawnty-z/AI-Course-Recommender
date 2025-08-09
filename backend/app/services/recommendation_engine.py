import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from collections import Counter
import math
import re
from datetime import datetime, timedelta
from functools import lru_cache

from ..models import CourseResponse
from ..database import execute_query
from ..config import settings
from .weaviate_service import weaviate_service

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Recommendation engine combining vector similarity and content-based signals"""
    
    def __init__(self):
        self.max_recommendations = settings.MAX_RECOMMENDATIONS
        self.min_similarity_score = settings.MIN_SIMILARITY_SCORE
        self._cache = {}
        self._cache_ttl = 300
    
    async def get_personalized_recommendations(
        self,
        user_id: int,
        query: Optional[str] = None,
        user_context: Dict[str, Any] = None,
        max_results: int = 10,
        force_refresh: bool = False
    ) -> List[CourseResponse]:
        """Get personalized recommendations (vector + content-based)"""
        try:
            cache_key = f"rec_{user_id}_{hash(str(query))}_{max_results}"
            if not force_refresh and cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                    logger.info(f"Returning cached recommendations for user {user_id}")
                    return cache_entry['data']
                else:
                    del self._cache[cache_key]
            
            if force_refresh and user_context:
                logger.info(f"Force refreshing recommendations for user {user_id}")
            
            vector_courses = await self._get_vector_recommendations(user_id, query, user_context)
            content_courses = await self._get_content_based_recommendations(user_id, query, user_context)
            
            combined_courses = self._combine_recommendations(vector_courses, content_courses)
            scored_courses = await self._score_courses(combined_courses, user_context, user_id)
            scored_courses.sort(key=lambda x: x[1], reverse=True)
            
            recommendations: List[CourseResponse] = []
            for course, score in scored_courses[:max_results]:
                course_response = CourseResponse(**course)
                course_response.similarity_score = round(score, 3)
                recommendations.append(course_response)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            
            self._cache[cache_key] = {
                'data': recommendations,
                'timestamp': datetime.now()
            }
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return await self._get_fallback_recommendations(max_results)
    
    async def _get_vector_recommendations(
        self,
        user_id: int,
        query: Optional[str],
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get candidates using vector search"""
        try:
            search_queries: List[str] = []
            exclude_topics: List[str] = []
            
            if query:
                search_queries.append(query)
                negative_patterns = [
                    r"don't want to learn ([^,.!?]+)",
                    r"not interested in ([^,.!?]+)",
                    r"avoid ([^,.!?]+)",
                    r"but not ([^,.!?]+)",
                    r"except ([^,.!?]+)",
                    r"without ([^,.!?]+)",
                    r"no ([^,.!?]+)",
                    r"I don't like ([^,.!?]+)"
                ]
                
                query_lower = query.lower()
                for pattern in negative_patterns:
                    matches = re.findall(pattern, query_lower)
                    for match in matches:
                        keywords = [word.strip() for word in match.split() if word.strip()]
                        exclude_topics.extend(keywords)
            
            if user_context and user_context.get('preferences'):
                prefs = user_context['preferences']
                if prefs.get('topics'):
                    topics_text = ' '.join(prefs['topics'])
                    search_queries.append(f"courses about {topics_text}")
                
                style_text = ""
                if prefs.get('learning_style'):
                    style_text += f"{prefs['learning_style']} learning"
                if prefs.get('difficulty'):
                    style_text += f" {prefs['difficulty']} level"
                if style_text.strip():
                    search_queries.append(style_text.strip())
            
            if user_context and user_context.get('recent_feedback'):
                positive_feedback = [f for f in user_context['recent_feedback'] if f.get('rating', 0) >= 4]
                current_prefs = user_context.get('preferences', {})
                if current_prefs.get('topics'):
                    logger.info(f"User {user_id} current preferences: {current_prefs['topics']}")
                if positive_feedback:
                    for feedback in positive_feedback[:3]:
                        course_id = feedback.get('course_id')
                        if course_id:
                            course = execute_query(
                                "SELECT title, description, topics FROM courses WHERE id = ?",
                                (course_id,),
                                fetch_one=True
                            )
                            if course:
                                topics = json.loads(course[2]) if course[2] else []
                                search_text = f"{course[0]} {' '.join(topics)}"
                                search_queries.append(search_text)
            
            combined_query = ' '.join(search_queries[:3]) if search_queries else "programming software development technology"
            
            vector_results = weaviate_service.search_similar_courses(
                combined_query,
                limit=max(15, self.max_recommendations * 2),
                min_certainty=0.4,
                exclude_topics=exclude_topics
            )
            
            candidates: List[Dict[str, Any]] = []
            for result in vector_results:
                candidates.append({
                    'id': result['id'],
                    'title': result['title'],
                    'description': result['description'],
                    'topics': result['topics'],
                    'difficulty': result['difficulty'],
                    'duration': result['duration'],
                    'format': result['format'],
                    'rating': result['rating'],
                    'vector_similarity': result['similarity_score']
                })
            
            logger.info(f"Vector search found {len(candidates)} courses for query: {combined_query[:100]}")
            return candidates
        except Exception as e:
            logger.error(f"Error in vector recommendations: {e}")
            return []
    
    async def _get_content_based_recommendations(
        self,
        user_id: int,
        query: Optional[str],
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get candidates using content-based filtering"""
        try:
            completed_courses = execute_query(
                "SELECT DISTINCT course_id FROM course_interactions WHERE user_id = ? AND interaction_type IN ('completed', 'dropped')",
                (user_id,)
            )
            completed_ids = [c[0] for c in completed_courses]
            
            low_rated = execute_query(
                "SELECT course_id FROM user_feedback WHERE user_id = ? AND rating <= 2",
                (user_id,)
            )
            low_rated_ids = [c[0] for c in low_rated]
            
            exclude_ids = set(completed_ids + low_rated_ids)
            
            base_query = "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses"
            params: List[Any] = []
            conditions: List[str] = []
            
            if query:
                conditions.append("(title LIKE ? OR description LIKE ? OR topics LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                conditions.append(f"id NOT IN ({placeholders})")
                params.extend(list(exclude_ids))
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            courses = execute_query(base_query, tuple(params))
            
            candidates: List[Dict[str, Any]] = []
            for course in courses:
                candidates.append({
                    'id': course[0],
                    'title': course[1],
                    'description': course[2],
                    'topics': json.loads(course[3]) if course[3] else [],
                    'difficulty': course[4],
                    'duration': course[5],
                    'format': course[6],
                    'rating': course[7],
                    'vector_similarity': 0.0
                })
            
            return candidates
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {e}")
            return []
    
    def _combine_recommendations(
        self,
        vector_courses: List[Dict[str, Any]],
        content_courses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate recommendations from different sources"""
        combined: Dict[str, Dict[str, Any]] = {}
        for course in vector_courses:
            course_id = course['id']
            combined[course_id] = course
            combined[course_id]['source'] = 'vector'
        for course in content_courses:
            course_id = course['id']
            if course_id not in combined:
                combined[course_id] = course
                combined[course_id]['source'] = 'content'
        return list(combined.values())
    
    async def _score_courses(
        self,
        courses: List[Dict],
        user_context: Dict[str, Any],
        user_id: int
    ) -> List[Tuple[Dict, float]]:
        """Score courses combining rating, vector similarity, and preference fit"""
        try:
            if not user_context:
                return [(course, course['rating'] / 5.0 + course.get('vector_similarity', 0.0) * 0.5) for course in courses]
            
            preferences = user_context.get('preferences', {})
            preferred_topics = preferences.get('topics', [])
            preferred_difficulty = preferences.get('difficulty')
            preferred_learning_style = preferences.get('learning_style')
            
            positive_topics = self._extract_positive_topic_patterns(user_context)
            
            scored_courses: List[Tuple[Dict, float]] = []
            for course in courses:
                score = 0.0
                base_score = course['rating'] / 5.0 * 0.2
                score += base_score
                vector_score = course.get('vector_similarity', 0.0) * 0.4
                score += vector_score
                topic_score = self._calculate_topic_score(
                    course['topics'], preferred_topics, positive_topics
                ) * 0.3
                score += topic_score
                difficulty_score = self._calculate_difficulty_score(
                    course['difficulty'], preferred_difficulty
                ) * 0.1
                score += difficulty_score
                style_score = self._calculate_learning_style_score(
                    course['format'], preferred_learning_style
                ) * 0.05
                score += style_score
                diversity_score = self._calculate_diversity_score(
                    course['topics'], preferred_topics
                ) * 0.05
                score += diversity_score
                if course.get('source') == 'vector':
                    score += 0.02
                scored_courses.append((course, score))
            return scored_courses
        except Exception as e:
            logger.error(f"Error in scoring: {e}")
            return [(course, course['rating'] / 5.0) for course in courses]
    
    def _calculate_topic_score(
        self,
        course_topics: List[str],
        preferred_topics: List[str],
        positive_topics: List[str]
    ) -> float:
        """Topic scoring with positive feedback weighting"""
        if not course_topics:
            return 0.0
        score = 0.0
        total_weight = 0.0
        for topic in course_topics:
            if topic.lower() in [p.lower() for p in preferred_topics]:
                score += 1.0
            total_weight += 1.0
        positive_counter = Counter([t.lower() for t in positive_topics])
        for topic in course_topics:
            topic_lower = topic.lower()
            if topic_lower in positive_counter:
                frequency_weight = min(positive_counter[topic_lower] / 3.0, 0.8)
                score += frequency_weight
        return min(score / max(len(course_topics), 1), 1.0)
    
    def _calculate_difficulty_score(self, course_difficulty: str, preferred_difficulty: Optional[str]) -> float:
        """Difficulty preference score"""
        if not preferred_difficulty or not course_difficulty:
            return 0.5
        if course_difficulty.lower() == preferred_difficulty.lower():
            return 1.0
        difficulty_levels = ['beginner', 'intermediate', 'advanced']
        try:
            course_idx = difficulty_levels.index(course_difficulty.lower())
            preferred_idx = difficulty_levels.index(preferred_difficulty.lower())
            distance = abs(course_idx - preferred_idx)
            if distance == 0:
                return 1.0
            elif distance == 1:
                return 0.7
            else:
                return 0.3
        except ValueError:
            return 0.5
    
    def _calculate_learning_style_score(self, course_format: str, preferred_style: Optional[str]) -> float:
        """Learning style compatibility score"""
        if not preferred_style or not course_format:
            return 0.5
        format_style_map = {
            'hands-on': ['hands-on', 'practical', 'project-based', 'interactive'],
            'video': ['visual', 'auditory', 'multimedia'],
            'interactive': ['hands-on', 'visual', 'engaging'],
            'text': ['reading', 'theoretical', 'self-paced'],
            'live': ['interactive', 'collaborative', 'social'],
            'project-based': ['hands-on', 'practical', 'applied']
        }
        preferred_lower = preferred_style.lower()
        course_format_lower = course_format.lower()
        if preferred_lower in course_format_lower:
            return 1.0
        for format_key, compatible_styles in format_style_map.items():
            if format_key in course_format_lower:
                if any(style in preferred_lower for style in compatible_styles):
                    return 0.8
        return 0.4
    
    def _calculate_diversity_score(self, course_topics: List[str], preferred_topics: List[str]) -> float:
        """Small bonus for exploring topics beyond current preferences"""
        if not course_topics or not preferred_topics:
            return 0.2
        new_topics = [t for t in course_topics if t.lower() not in [p.lower() for p in preferred_topics]]
        diversity_ratio = len(new_topics) / len(course_topics)
        return diversity_ratio * 0.5
    
    def _extract_positive_topic_patterns(self, user_context: Dict[str, Any]) -> List[str]:
        """Extract topics from positively-rated courses"""
        positive_topics: List[str] = []
        for feedback in user_context.get('recent_feedback', []):
            if feedback.get('rating', 0) >= 4:
                course_id = feedback.get('course_id')
                if course_id:
                    course = execute_query(
                        "SELECT topics FROM courses WHERE id = ?",
                        (course_id,),
                        fetch_one=True
                    )
                    if course and course[0]:
                        topics = json.loads(course[0])
                        positive_topics.extend(topics)
        return positive_topics
    
    async def get_similar_courses_vector(
        self,
        course_id: str,
        max_results: int = 5
    ) -> List[CourseResponse]:
        """Get similar courses via vector similarity"""
        try:
            target_course = execute_query(
                "SELECT title, description, topics FROM courses WHERE id = ?",
                (course_id,),
                fetch_one=True
            )
            if not target_course:
                return []
            topics = json.loads(target_course[2]) if target_course[2] else []
            search_query = f"{target_course[0]} {target_course[1]} {' '.join(topics)}"
            similar_courses = weaviate_service.search_similar_courses(
                search_query,
                limit=max_results + 1,
                min_certainty=0.4
            )
            result: List[CourseResponse] = []
            for course in similar_courses:
                if course['id'] != course_id:
                    course_response = CourseResponse(
                        id=course['id'],
                        title=course['title'],
                        description=course['description'],
                        topics=course['topics'],
                        difficulty=course['difficulty'],
                        duration=course['duration'],
                        format=course['format'],
                        rating=course['rating'],
                        similarity_score=course['similarity_score']
                    )
                    result.append(course_response)
                    if len(result) >= max_results:
                        break
            return result
        except Exception as e:
            logger.error(f"Error finding vector-based similar courses: {e}")
            return []
    
    async def _get_fallback_recommendations(self, max_results: int) -> List[CourseResponse]:
        """Fallback based on top-rated courses"""
        try:
            courses = execute_query(
                "SELECT id, title, description, topics, difficulty, duration, format, rating FROM courses ORDER BY rating DESC LIMIT ?",
                (max_results,)
            )
            result: List[CourseResponse] = []
            for course in courses:
                result.append(CourseResponse(
                    id=course[0],
                    title=course[1],
                    description=course[2],
                    topics=json.loads(course[3]) if course[3] else [],
                    difficulty=course[4],
                    duration=course[5],
                    format=course[6],
                    rating=course[7],
                    similarity_score=course[7] / 5.0
                ))
            return result
        except Exception as e:
            logger.error(f"Error getting fallback recommendations: {e}")
            return []

# Global instance
recommendation_engine = RecommendationEngine() 