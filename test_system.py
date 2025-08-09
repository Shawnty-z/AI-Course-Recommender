#!/usr/bin/env python3
"""
Quick system test to verify the AI Course Recommender is working
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if the backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 8000?")
        return False

def test_ollama():
    """Test if Ollama is accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json()
            if any("llama3.2:1b" in model.get("name", "") for model in models.get("models", [])):
                print("✅ Ollama and Llama 3.2 1B model available")
                return True
            else:
                print("❌ Llama 3.2 1B model not found in Ollama")
                return False
        else:
            print(f"❌ Ollama health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running on port 11434?")
        return False

def test_auth():
    """Test authentication system"""
    try:
        # Test login with demo user - using query parameter
        response = requests.post(f"{BASE_URL}/api/auth/login?username=demo_user")
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authentication system working")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return None

def test_courses(token):
    """Test course endpoints"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/courses/", headers=headers)
        
        if response.status_code == 200:
            courses = response.json()
            print(f"✅ Course catalog loaded ({len(courses)} courses)")
            return len(courses) > 0
        else:
            print(f"❌ Course loading failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Course test failed: {e}")
        return False

def test_recommendations(token):
    """Test recommendation system"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test getting recommendations for demo user (ID: 1)
        response = requests.get(f"{BASE_URL}/api/recommendations/1", headers=headers)
        
        if response.status_code == 200:
            recommendations = response.json()
            courses = recommendations.get("courses", [])
            reasoning = recommendations.get("reasoning")
            
            print(f"✅ Recommendation system working ({len(courses)} recommendations)")
            if reasoning:
                print(f"✅ LLM reasoning generated: {reasoning[:100]}...")
            else:
                print("⚠️  LLM reasoning not generated (Ollama might be slow)")
            
            return len(courses) > 0
        else:
            print(f"❌ Recommendation test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Recommendation test failed: {e}")
        return False

def test_feedback(token):
    """Test feedback system"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Submit test feedback
        feedback_data = {
            "course_id": "python-fundamentals",
            "rating": 5,
            "feedback_text": "Test feedback from system check",
            "learning_style": "hands-on",
            "difficulty_preference": "beginner"
        }
        
        response = requests.post(f"{BASE_URL}/api/feedback/", 
                               json=feedback_data, 
                               headers=headers)
        
        if response.status_code == 200:
            print("✅ Feedback system working")
            return True
        else:
            print(f"❌ Feedback test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Feedback test failed: {e}")
        return False

def main():
    print("🎓 AI Course Recommender System Test")
    print("====================================")
    
    tests_passed = 0
    total_tests = 6
    
    # Test backend health
    if test_health():
        tests_passed += 1
    
    # Test Ollama
    if test_ollama():
        tests_passed += 1
    
    # Test authentication
    token = test_auth()
    if token:
        tests_passed += 1
        
        # Test courses (requires auth)
        if test_courses(token):
            tests_passed += 1
        
        # Test recommendations (requires auth)
        if test_recommendations(token):
            tests_passed += 1
        
        # Test feedback (requires auth)
        if test_feedback(token):
            tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All systems operational! Ready for demo.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 