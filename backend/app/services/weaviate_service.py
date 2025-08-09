import weaviate
from weaviate.classes.config import Configure
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import os

from ..config import settings

logger = logging.getLogger(__name__)

class WeaviateService:
    def __init__(self):
        """Initialize Weaviate client and embedding model"""
        self.client = None
        self.embedding_model = None
        self.synonym_mappings: Dict[str, str] = {}
        self._initialize_client()
        self._initialize_embedding_model()
        self._load_synonyms()
    
    def _initialize_client(self):
        """Initialize Weaviate client with connection"""
        try:
            # Connect to Weaviate using v4 API
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080
            )
            if self.client.is_ready():
                logger.info("Successfully connected to Weaviate v4")
            else:
                logger.warning("Weaviate client created but server not ready")
        except Exception as e:
            logger.error(f"Error initializing Weaviate client: {e}")
            self.client = None
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
    
    def _load_synonyms(self) -> None:
        """Load synonym mappings from config/synonyms.json with safe fallback"""
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            synonyms_path = os.path.join(base_dir, "config", "synonyms.json")
            if os.path.exists(synonyms_path):
                with open(synonyms_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.synonym_mappings = {str(k).lower(): str(v) for k, v in data.items()}
                        logger.info(f"Loaded {len(self.synonym_mappings)} synonym mappings from config")
                        return
            # Fallback minimal mappings
            self.synonym_mappings = {
                'website': 'website web development web app',
                'webapp': 'webapp web application web development',
                'full stack': 'full stack web development frontend backend database',
                'software engineer': 'software engineer developer programmer coding programming'
            }
            logger.warning("Synonym config not found; using minimal defaults")
        except Exception as e:
            logger.error(f"Error loading synonyms: {e}")
            self.synonym_mappings = {}
    
    def create_schema(self):
        """Create Weaviate schema for courses and user preferences"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping schema creation")
            return False
            
        try:
            # Delete existing collections if they exist
            try:
                self.client.collections.delete("Course")
                logger.info("Deleted existing Course collection")
            except:
                pass
                
            try:
                self.client.collections.delete("UserPreference")
                logger.info("Deleted existing UserPreference collection")
            except:
                pass
            
            # Create Course collection
            self.client.collections.create(
                name="Course",
                description="AI Course catalog with vector embeddings",
                vectorizer_config=Configure.Vectorizer.none(),  # We'll provide our own vectors
                properties=[
                    weaviate.classes.config.Property(
                        name="courseId",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Unique course identifier"
                    ),
                    weaviate.classes.config.Property(
                        name="title",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Course title"
                    ),
                    weaviate.classes.config.Property(
                        name="description",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Detailed course description"
                    ),
                    weaviate.classes.config.Property(
                        name="topics",
                        data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                        description="Course topic tags"
                    ),
                    weaviate.classes.config.Property(
                        name="difficulty",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Course difficulty level"
                    ),
                    weaviate.classes.config.Property(
                        name="duration",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Course duration"
                    ),
                    weaviate.classes.config.Property(
                        name="format",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Course format (hands-on, video, etc.)"
                    ),
                    weaviate.classes.config.Property(
                        name="rating",
                        data_type=weaviate.classes.config.DataType.NUMBER,
                        description="Average course rating"
                    ),
                    weaviate.classes.config.Property(
                        name="contentVector",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Text used for vector embedding"
                    )
                ]
            )
            
            # Create UserPreference collection
            self.client.collections.create(
                name="UserPreference",
                description="User learning preferences with vector embeddings",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    weaviate.classes.config.Property(
                        name="userId",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="User identifier"
                    ),
                    weaviate.classes.config.Property(
                        name="preferenceText",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="User preference description"
                    ),
                    weaviate.classes.config.Property(
                        name="topicsLiked",
                        data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                        description="Topics user has shown interest in"
                    ),
                    weaviate.classes.config.Property(
                        name="topicsDisliked",
                        data_type=weaviate.classes.config.DataType.TEXT_ARRAY,
                        description="Topics user has shown disinterest in"
                    ),
                    weaviate.classes.config.Property(
                        name="learningStyle",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Preferred learning style"
                    ),
                    weaviate.classes.config.Property(
                        name="difficultyLevel",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        description="Preferred difficulty level"
                    ),
                    weaviate.classes.config.Property(
                        name="timestamp",
                        data_type=weaviate.classes.config.DataType.DATE,
                        description="When preference was created/updated"
                    )
                ]
            )
            
            logger.info("Successfully created Weaviate collections")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Weaviate schema: {e}")
            return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence transformer"""
        if not self.embedding_model:
            return []
            
        try:
            # Clean and prepare text
            clean_text = text.strip().replace('\n', ' ').replace('\r', ' ')
            if not clean_text:
                return []
                
            # Generate embedding
            embedding = self.embedding_model.encode(clean_text)
            
            # Convert to list for JSON serialization
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def add_course(self, course_data: Dict[str, Any]) -> bool:
        """Add course to Weaviate with vector embedding"""
        if not self.client:
            logger.warning("Weaviate client not available")
            return False
            
        try:
            # Create content text for embedding
            content_parts = [
                course_data.get('title', ''),
                course_data.get('description', ''),
                ' '.join(course_data.get('topics', [])),
                course_data.get('difficulty', ''),
                course_data.get('format', '')
            ]
            content_text = ' '.join(filter(None, content_parts))
            
            # Generate embedding
            vector = self.generate_embedding(content_text)
            
            if not vector:
                logger.warning(f"Could not generate embedding for course {course_data.get('id')}")
                return False
            
            # Prepare data for Weaviate
            weaviate_data = {
                "courseId": course_data.get('id'),
                "title": course_data.get('title'),
                "description": course_data.get('description'),
                "topics": course_data.get('topics', []),
                "difficulty": course_data.get('difficulty'),
                "duration": course_data.get('duration'),
                "format": course_data.get('format'),
                "rating": float(course_data.get('rating', 0.0)),
                "contentVector": content_text
            }
            
            # Add to Weaviate using v4 API
            course_collection = self.client.collections.get("Course")
            uuid = course_collection.data.insert(
                properties=weaviate_data,
                vector=vector
            )
            
            logger.info(f"Added course {course_data.get('id')} to Weaviate: {uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding course to Weaviate: {e}")
            return False
    
    def search_similar_courses(
        self, 
        query_text: str, 
        limit: int = 10,
        min_certainty: float = 0.4,
        exclude_topics: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar courses using vector similarity with negative filtering"""
        if not self.client:
            logger.warning("Weaviate client not available")
            return []
            
        try:
            # Parse negative preferences from query
            negative_keywords = self._extract_negative_keywords(query_text)
            if exclude_topics:
                negative_keywords.extend(exclude_topics)
            
            # Clean query for embedding (remove negative phrases)
            clean_query = self._clean_query_for_embedding(query_text)
            
            # Generate embedding for cleaned query
            query_vector = self.generate_embedding(clean_query)
            
            if not query_vector:
                logger.warning("Could not generate embedding for query")
                return []
            
            # Get the Course collection
            course_collection = self.client.collections.get("Course")
            
            # Perform vector search using v4 API - get more results to allow for filtering
            search_limit = limit * 3  # Get more results to account for filtering
            result = course_collection.query.near_vector(
                near_vector=query_vector,
                limit=search_limit,
                distance=1.0 - min_certainty,  # Convert certainty to distance
                return_metadata=["distance"]
            )
            
            # Format results with negative filtering
            formatted_courses = []
            for obj in result.objects:
                props = obj.properties
                distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
                certainty = 1.0 - distance
                
                if certainty >= min_certainty:
                    # Check if course should be excluded based on negative keywords
                    if not self._should_exclude_course(props, negative_keywords):
                        formatted_courses.append({
                            'id': props.get('courseId'),
                            'title': props.get('title'),
                            'description': props.get('description'),
                            'topics': props.get('topics', []),
                            'difficulty': props.get('difficulty'),
                            'duration': props.get('duration'),
                            'format': props.get('format'),
                            'rating': props.get('rating'),
                            'similarity_score': certainty,
                            'distance': distance
                        })
                        
                        # Stop when we have enough results
                        if len(formatted_courses) >= limit:
                            break
            
            logger.info(f"Found {len(formatted_courses)} similar courses (filtered {len(result.objects) - len(formatted_courses)} excluded courses)")
            return formatted_courses
            
        except Exception as e:
            logger.error(f"Error searching similar courses: {e}")
            return []
    
    def _extract_negative_keywords(self, query_text: str) -> List[str]:
        """Extract negative keywords from query text"""
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
        
        import re
        negative_keywords = []
        query_lower = query_text.lower()
        
        for pattern in negative_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                # Split multi-word matches and clean them
                keywords = [word.strip() for word in match.split() if word.strip()]
                negative_keywords.extend(keywords)
        
        # Also check for simple "not X" patterns
        not_pattern = r"not (\w+)"
        not_matches = re.findall(not_pattern, query_lower)
        negative_keywords.extend(not_matches)
        
        return list(set(negative_keywords))  # Remove duplicates
    
    def _clean_query_for_embedding(self, query_text: str) -> str:
        """Remove negative phrases from query for better embedding and expand synonyms"""
        import re
        
        # Remove negative phrases
        negative_patterns = [
            r"don't want to learn [^,.!?]+",
            r"not interested in [^,.!?]+",
            r"but not [^,.!?]+",
            r"avoid [^,.!?]+",
            r"except [^,.!?]+",
            r"without [^,.!?]+",
            r"I don't like [^,.!?]+",
            r"not \w+"
        ]
        
        clean_query = query_text
        for pattern in negative_patterns:
            clean_query = re.sub(pattern, "", clean_query, flags=re.IGNORECASE)
        
        # Apply synonym expansion from config
        query_lower = clean_query.lower()
        for synonym, expansion in self.synonym_mappings.items():
            if synonym in query_lower:
                clean_query = clean_query.replace(synonym, expansion)
                break
        
        # Clean up extra spaces and punctuation
        clean_query = re.sub(r'\s+', ' ', clean_query).strip()
        clean_query = re.sub(r'^[,.\s]+|[,.\s]+$', '', clean_query)
        
        # If query becomes empty or too short, use a generic programming query
        if len(clean_query.strip()) < 3:
            clean_query = "programming software development"
            
        return clean_query
    
    def _should_exclude_course(self, course_props: Dict, negative_keywords: List[str]) -> bool:
        """Check if course should be excluded based on negative keywords"""
        if not negative_keywords:
            return False
        
        # Only check exact word matches in title and explicit topic tags (avoid substring matches in description)
        import re
        title_text = course_props.get('title', '').lower()
        title_tokens = set(re.findall(r"\b\w+\b", title_text))
        topics = course_props.get('topics', [])
        topic_tokens = set([t.lower() for t in topics]) if isinstance(topics, list) else set()
        
        for keyword in negative_keywords:
            kw = keyword.lower().strip()
            if len(kw) < 3:
                continue
            if kw in topic_tokens or kw in title_tokens:
                logger.info(f"Excluding course due to negative keyword '{kw}': {course_props.get('title')}")
                return True
        
        return False
    
    def add_user_preference(self, user_id: str, preference_data: Dict[str, Any]) -> bool:
        """Add or update user preferences in Weaviate"""
        if not self.client:
            return False
            
        try:
            # Create preference text for embedding
            preference_parts = [
                ' '.join(preference_data.get('topics_liked', [])),
                preference_data.get('learning_style', ''),
                preference_data.get('difficulty_level', ''),
                preference_data.get('feedback_summary', '')
            ]
            preference_text = ' '.join(filter(None, preference_parts))
            
            # Generate embedding
            vector = self.generate_embedding(preference_text)
            
            if not vector:
                return False
            
            user_pref_collection = self.client.collections.get("UserPreference")
            
            # Check if user preference already exists
            existing = user_pref_collection.query.fetch_objects(limit=1)
            
            weaviate_data = {
                "userId": user_id,
                "preferenceText": preference_text,
                "topicsLiked": preference_data.get('topics_liked', []),
                "topicsDisliked": preference_data.get('topics_disliked', []),
                "learningStyle": preference_data.get('learning_style', ''),
                "difficultyLevel": preference_data.get('difficulty_level', ''),
                "timestamp": preference_data.get('timestamp', '2024-01-01T00:00:00Z')
            }
            
            if existing.objects:
                # Update existing preference
                uuid_to_update = existing.objects[0].uuid
                user_pref_collection.data.replace(
                    uuid=uuid_to_update,
                    properties=weaviate_data,
                    vector=vector
                )
                logger.info(f"Updated user preference for user {user_id}")
            else:
                # Create new preference
                user_pref_collection.data.insert(
                    properties=weaviate_data,
                    vector=vector
                )
                logger.info(f"Created user preference for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding user preference: {e}")
            return False
    
    def find_users_with_similar_preferences(
        self, 
        user_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find users with similar learning preferences"""
        if not self.client:
            return []
            
        try:
            user_pref_collection = self.client.collections.get("UserPreference")
            
            # Get current user's preference
            user_pref = user_pref_collection.query.fetch_objects(
                where=weaviate.classes.query.Filter.by_property("userId").equal(user_id),
                limit=1,
                include_vector=True
            )
            
            if not user_pref.objects:
                return []
            
            user_vector = user_pref.objects[0].vector
            if not user_vector:
                return []
            
            # Find similar users
            similar_users = user_pref_collection.query.near_vector(
                near_vector=user_vector,
                limit=limit + 1,  # +1 to exclude self
                distance=0.4,  # Allow moderate similarity
                return_metadata=["distance"]
            )
            
            # Filter out the current user
            similar_users_list = []
            for obj in similar_users.objects:
                props = obj.properties
                if props.get('userId') != user_id:
                    distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
                    similar_users_list.append({
                        'user_id': props.get('userId'),
                        'topics_liked': props.get('topicsLiked', []),
                        'learning_style': props.get('learningStyle'),
                        'similarity': 1.0 - distance
                    })
            
            return similar_users_list[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []
    
    def get_recommended_courses_by_user_similarity(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get course recommendations based on similar users (collaborative filtering)"""
        try:
            # Find users with similar preferences
            similar_users = self.find_users_with_similar_preferences(user_id, limit=5)
            
            if not similar_users:
                return []
            
            # This would require integration with the main database to see what courses
            # similar users have liked/enrolled in. For now, return empty list.
            # In a full implementation, you would:
            # 1. Get courses that similar users have rated highly
            # 2. Filter out courses the current user has already seen/enrolled in
            # 3. Return recommendations with similarity weighting
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check Weaviate connection health"""
        if not self.client:
            return {
                "status": "disconnected",
                "message": "Weaviate client not initialized"
            }
        
        try:
            is_ready = self.client.is_ready()
            
            # Get collections (equivalent to classes in v3)
            collections = []
            try:
                collections = list(self.client.collections.list_all().keys())
            except:
                pass
            
            return {
                "status": "connected" if is_ready else "error",
                "ready": is_ready,
                "collections": collections,
                "embedding_model": settings.EMBEDDING_MODEL if self.embedding_model else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def __del__(self):
        """Clean up Weaviate connection"""
        if self.client:
            try:
                self.client.close()
            except:
                pass

# Global instance
weaviate_service = WeaviateService() 