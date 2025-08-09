#!/usr/bin/env python3
"""
Test script for AI Course Recommender API endpoints
Run this to test all recommendation functions with various inputs
"""

import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000"
DEMO_USER_ID = 1

# Test authentication first
def get_auth_token():
    """Get authentication token for demo user"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", 
                               params={"username": "demo_user"})
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_recommendations():
    """Test all recommendation endpoints"""
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🚀 Testing AI Course Recommender API")
    print("=" * 50)
    
    # Test 1: Default Personalized Recommendations
    print("\n📋 Test 1: Default Personalized Recommendations")
    print("-" * 40)
    print("Endpoint: GET /api/recommendations/{user_id}")
    print("Description: Get personalized recommendations based on user profile")
    
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data['courses'])} recommendations")
            print(f"🤖 AI Reasoning: {data['reasoning'][:100]}...")
            print(f"👤 User Context: {data['user_context']['preferences']['topics']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Query-Based Recommendations
    print("\n📋 Test 2: Query-Based Recommendations")
    print("-" * 40)
    print("Endpoint: POST /api/recommendations/{user_id}")
    print("Description: Get recommendations for specific query")
    
    test_queries = [
        "I want to learn machine learning",
        "Show me web development courses",
        "I need beginner Python courses",
        "I want to learn data science but not statistics",
        "Help me with mobile app development"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test 2.{i}: '{query}'")
        try:
            payload = {
                "query": query,
                "max_results": 5,
                "include_reasoning": True
            }
            response = requests.post(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}", 
                                   headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                courses = data.get('courses') or []
                reasoning = data.get('reasoning') or ''
                print(f"✅ Found {len(courses)} courses")
                if reasoning:
                    print(f"🤖 AI Reasoning: {reasoning[:80]}...")
                for course in courses[:2]:  # Show first 2 courses
                    print(f"   📚 {course['title']} (Score: {course.get('similarity_score')})")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 3: Pure Semantic Search
    print("\n📋 Test 3: Pure Semantic Search")
    print("-" * 40)
    print("Endpoint: POST /api/recommendations/{user_id}/semantic-search")
    print("Description: Direct vector similarity search")
    
    semantic_queries = [
        "machine learning algorithms",
        "python programming basics",
        "web development with JavaScript",
        "data analysis and visualization",
        "cybersecurity fundamentals"
    ]
    
    for i, query in enumerate(semantic_queries, 1):
        print(f"\n🔍 Test 3.{i}: '{query}'")
        try:
            params = {
                "query": query,
                "max_results": 3,
                "min_similarity": 0.4
            }
            response = requests.post(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}/semantic-search", 
                                   headers=headers, params=params)
            if response.status_code == 200:
                courses = response.json()
                print(f"✅ Found {len(courses)} courses")
                for course in courses:
                    print(f"   📚 {course['title']} (Similarity: {course['similarity_score']})")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 4: Similar Courses (Vector-Based)
    print("\n📋 Test 4: Similar Courses (Vector-Based)")
    print("-" * 40)
    print("Endpoint: POST /api/recommendations/{user_id}/similar")
    print("Description: Find courses similar to a specific course")
    
    test_courses = [
        "python-fundamentals",
        "machine-learning-intro", 
        "web-development-react"
    ]
    
    for i, course_id in enumerate(test_courses, 1):
        print(f"\n🔍 Test 4.{i}: Similar to '{course_id}'")
        try:
            params = {
                "course_id": course_id,
                "max_results": 3,
                "use_vector_search": True
            }
            response = requests.post(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}/similar", 
                                   headers=headers, params=params)
            if response.status_code == 200:
                courses = response.json()
                print(f"✅ Found {len(courses)} similar courses")
                for course in courses:
                    print(f"   📚 {course['title']} (Similarity: {course['similarity_score']})")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 5: Negative Preference Handling
    print("\n📋 Test 5: Negative Preference Handling")
    print("-" * 40)
    print("Description: Test queries with negative preferences")
    
    negative_queries = [
        "I want to learn data science but not statistics",
        "Show me programming courses but not web development",
        "I need machine learning courses without heavy math",
        "Python courses but not advanced topics"
    ]
    
    for i, query in enumerate(negative_queries, 1):
        print(f"\n🔍 Test 5.{i}: '{query}'")
        try:
            payload = {
                "query": query,
                "max_results": 3,
                "include_reasoning": True
            }
            response = requests.post(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}", 
                                   headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('courses'):
                    print(f"✅ Found {len(data['courses'])} courses")
                    if data.get('reasoning'):
                        print(f"🤖 AI Reasoning: {data['reasoning'][:100]}...")
                    for course in data['courses']:
                        print(f"   📚 {course['title']}")
                else:
                    print(f"⚠️ No courses found (negative filtering may be too restrictive)")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 6: Recommendation History
    print("\n📋 Test 6: Recommendation History")
    print("-" * 40)
    print("Endpoint: GET /api/recommendations/{user_id}/history")
    print("Description: Get user's recommendation history and patterns")
    
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/{DEMO_USER_ID}/history", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User History Retrieved")
            print(f"📊 Total Feedback: {data.get('total_feedback', 0)}")
            print(f"⭐ Average Rating: {data.get('avg_rating', 0):.1f}")
            print(f"🎯 Preferred Topics: {data.get('preferred_topics', [])}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_curl_examples():
    """Print curl examples for manual testing"""
    print("\n" + "=" * 60)
    print("🔄 CURL EXAMPLES FOR MANUAL TESTING")
    print("=" * 60)
    
    # Get token first
    token = get_auth_token()
    if not token:
        print("❌ Cannot generate curl examples without authentication")
        return
    
    print(f"\n🔑 Authentication Token: {token}")
    print("\n📋 Example 1: Default Recommendations")
    print(f"""curl -X GET "http://localhost:8000/api/recommendations/1" \\
     -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" """)
    
    print("\n📋 Example 2: Query-Based Recommendations")
    print(f"""curl -X POST "http://localhost:8000/api/recommendations/1" \\
     -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" \\
     -d '{{"query": "I want to learn machine learning", "max_results": 5, "include_reasoning": true}}' """)
    
    print("\n📋 Example 3: Semantic Search")
    print(f"""curl -X POST "http://localhost:8000/api/recommendations/1/semantic-search?query=machine+learning&max_results=3&min_similarity=0.4" \\
     -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" """)
    
    print("\n📋 Example 4: Similar Courses")
    print(f"""curl -X POST "http://localhost:8000/api/recommendations/1/similar" \\
     -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" \\
     -d '{{"course_id": "python-fundamentals", "max_results": 3, "use_vector_search": true}}' """)
    
    print("\n📋 Example 5: Negative Preferences")
    print(f"""curl -X POST "http://localhost:8000/api/recommendations/1" \\
     -H "Authorization: Bearer {token}" \\
     -H "Content-Type: application/json" \\
     -d '{{"query": "I want data science but not statistics", "max_results": 3, "include_reasoning": true}}' """)

if __name__ == "__main__":
    print("🎯 AI Course Recommender - API Testing Suite")
    print("Make sure the backend is running on http://localhost:8000")
    print("Make sure Weaviate is running on http://localhost:8080")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    # Run tests
    test_recommendations()
    
    # Show curl examples
    test_curl_examples()
    
    print("\n🎉 Testing complete! Check the results above.")
    print("\n💡 Tips for Interview Demo:")
    print("1. Show the semantic search understanding intent")
    print("2. Demonstrate negative preference handling")
    print("3. Highlight the AI reasoning explanations")
    print("4. Show how recommendations change with different queries") 