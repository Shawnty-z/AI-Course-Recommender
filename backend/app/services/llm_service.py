import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

from ..config import settings
from ..models import CourseResponse

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self._cache = {}  # In-memory cache for reasoning
        self._cache_ttl = 600  # 10 minutes cache TTL
        
    async def generate_recommendation_reasoning(
        self,
        recommendations: List[CourseResponse],
        user_context: Dict[str, Any],
        query: Optional[str] = None
    ) -> str:
        """Generate reasoning for course recommendations using LLM"""
        try:
            logger.info(f"Generating reasoning for {len(recommendations)} recommendations")
            
            # Check cache first
            cache_key = f"reasoning_{hash(str([r.id for r in recommendations]))}_{hash(str(user_context.get('preferences', {})))}"
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                    logger.info("Returning cached reasoning")
                    return cache_entry['data']
                else:
                    del self._cache[cache_key]
            
            # Build context prompt
            try:
                prompt = self._build_recommendation_prompt(recommendations, user_context, query)
                logger.info(f"Generated prompt length: {len(prompt)} characters")
            except Exception as prompt_error:
                logger.error(f"Error building prompt: {prompt_error}")
                # Fallback to simple prompt
                course_titles = [course.title for course in recommendations[:3]]
                user_topics = user_context.get('preferences', {}).get('topics', [])
                prompt = f"""
                I'm recommending these courses: {', '.join(course_titles)}
                
                The user is interested in: {', '.join(user_topics)}
                
                Please explain why these courses are a good match for this user in 2-3 sentences.
                """
                logger.info(f"Using fallback prompt: {len(prompt)} characters")
            
            # Call Ollama
            logger.info("Calling Ollama for reasoning generation...")
            response = await self._call_ollama(prompt)
            logger.info(f"Ollama response length: {len(response)} characters")
            
            # Cache the result
            self._cache[cache_key] = {
                'data': response.strip(),
                'timestamp': datetime.now()
            }
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating recommendation reasoning: {e}")
            return "I've selected these courses based on your preferences and learning history."
    
    async def generate_course_suggestions(
        self,
        user_context: Dict[str, Any],
        query: str
    ) -> str:
        """Generate course suggestions based on user query"""
        try:
            prompt = f"""
            Based on the user's learning profile and query, suggest relevant courses.
            
            User Profile:
            - Preferred Topics: {user_context.get('preferences', {}).get('topics', [])}
            - Learning Style: {user_context.get('preferences', {}).get('learning_style', 'Not specified')}
            - Difficulty Preference: {user_context.get('preferences', {}).get('difficulty', 'Not specified')}
            - Recent Positive Feedback: {[f for f in user_context.get('recent_feedback', []) if f.get('rating', 0) >= 4]}
            
            User Query: "{query}"
            
            Please suggest course topics and learning approaches that would be most suitable for this user. 
            Focus on actionable recommendations.
            """
            
            response = await self._call_ollama(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating course suggestions: {e}")
            return "Based on your preferences, I recommend exploring courses in your areas of interest."
    
    async def analyze_learning_patterns(self, user_context: Dict[str, Any]) -> str:
        """Analyze user's learning patterns and preferences"""
        try:
            prompt = f"""
            Analyze this user's learning patterns and provide insights:
            
            Learning History:
            - Preferred Topics: {user_context.get('preferences', {}).get('topics', [])}
            - Learning Style: {user_context.get('preferences', {}).get('learning_style', 'Not specified')}
            - Recent Feedback: {user_context.get('recent_feedback', [])}
            - Recent Interactions: {user_context.get('recent_interactions', [])}
            
            Provide a brief analysis of:
            1. Learning preferences
            2. Strengths and interests
            3. Areas for improvement
            4. Recommended learning approach
            
            Keep it concise and actionable.
            """
            
            response = await self._call_ollama(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return "Based on your activity, you show consistent engagement with your preferred topics."
    
    def _build_recommendation_prompt(
        self,
        recommendations: List[CourseResponse],
        user_context: Dict[str, Any],
        query: Optional[str] = None
    ) -> str:
        """Build a comprehensive prompt for recommendation reasoning"""
        
        # Format course information (simplified)
        courses_text = ""
        for i, course in enumerate(recommendations[:3], 1):  # Limit to 3 courses
            courses_text += f"{i}. {course.title} ({course.difficulty}, {course.rating}/5.0)\n"
        
        # Format user preferences
        prefs = user_context.get('preferences', {})
        user_topics = prefs.get('topics', ['Not specified'])
        user_difficulty = prefs.get('difficulty', 'Not specified')
        
        # Build the complete prompt (simplified)
        prompt = f"""
        User interests: {', '.join(user_topics)}
        Preferred difficulty: {user_difficulty}

        Recommended courses:
        {courses_text}

        In 2-3 concise sentences, explain why these courses align with the user's interests and goals. Avoid marketing language.
        """
        
        return prompt.strip()
    
    def _format_recent_activity(self, recent_feedback: List[Dict]) -> str:
        """Format recent feedback for the prompt"""
        if not recent_feedback:
            return "No recent course feedback available."
        
        activity = []
        for feedback in recent_feedback[:5]:
            rating = feedback.get('rating', 0)
            sentiment = "loved" if rating >= 4 else "had mixed feelings about" if rating >= 3 else "struggled with"
            activity.append(f"- {sentiment} a course (rated {rating}/5)")
            
            if feedback.get('feedback_text'):
                activity.append(f"  Comment: {feedback['feedback_text'][:100]}...")
        
        return '\n'.join(activity)
    
    async def _call_ollama(self, prompt: str, max_tokens: int = 300) -> str:
        """Make a request to Ollama API"""
        try:
            logger.info(f"Making Ollama request with {len(prompt)} character prompt")
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                }
                
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=10.0  # Reduced from 30s to 10s
                )
                
                response.raise_for_status()
                result = response.json()
                
                response_text = result.get("response", "I'm having trouble generating a response right now.")
                logger.info(f"Ollama response length: {len(response_text)} characters")
                
                return response_text
                
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return "I've selected these courses based on your preferences and learning history."
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Ollama: {e}")
            return "These courses are recommended based on your learning profile."
            
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            return "These courses are selected based on your preferences and learning history." 