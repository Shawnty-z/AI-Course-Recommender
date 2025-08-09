#!/usr/bin/env python3
"""
Script to populate the database with sample course data
"""

import sqlite3
import json
from pathlib import Path

# Sample courses data
SAMPLE_COURSES = [
    {
        "id": "python-fundamentals",
        "title": "Python Programming Fundamentals",
        "description": "Learn the basics of Python programming including variables, functions, loops, and data structures. Perfect for absolute beginners.",
        "topics": ["python", "programming", "fundamentals", "variables", "functions"],
        "difficulty": "beginner",
        "duration": "4 weeks",
        "format": "interactive",
        "rating": 4.5
    },
    {
        "id": "machine-learning-intro",
        "title": "Introduction to Machine Learning",
        "description": "Discover the world of machine learning with hands-on projects using Python. Build your first ML models and understand key concepts.",
        "topics": ["machine learning", "python", "data science", "algorithms", "models"],
        "difficulty": "intermediate",
        "duration": "8 weeks",
        "format": "hands-on",
        "rating": 4.7
    },
    {
        "id": "web-development-react",
        "title": "Modern Web Development with React",
        "description": "Build interactive web applications using React, JavaScript, and modern web development practices.",
        "topics": ["react", "javascript", "web development", "frontend", "components"],
        "difficulty": "intermediate",
        "duration": "6 weeks",
        "format": "project-based",
        "rating": 4.4
    },
    {
        "id": "data-structures-algorithms",
        "title": "Data Structures and Algorithms",
        "description": "Master fundamental computer science concepts including arrays, linked lists, trees, graphs, and sorting algorithms.",
        "topics": ["data structures", "algorithms", "computer science", "programming", "problem solving"],
        "difficulty": "intermediate",
        "duration": "10 weeks",
        "format": "theoretical",
        "rating": 4.3
    },
    {
        "id": "sql-database-design",
        "title": "SQL and Database Design",
        "description": "Learn to design, create, and query databases using SQL. Understand relational database concepts and best practices.",
        "topics": ["sql", "databases", "data modeling", "queries", "relational databases"],
        "difficulty": "beginner",
        "duration": "5 weeks",
        "format": "hands-on",
        "rating": 4.2
    },
    {
        "id": "advanced-python",
        "title": "Advanced Python Programming",
        "description": "Deep dive into advanced Python concepts including decorators, metaclasses, async programming, and performance optimization.",
        "topics": ["python", "advanced programming", "decorators", "async", "optimization"],
        "difficulty": "advanced",
        "duration": "6 weeks",
        "format": "hands-on",
        "rating": 4.6
    },
    {
        "id": "data-visualization",
        "title": "Data Visualization with Python",
        "description": "Create compelling data visualizations using matplotlib, seaborn, and plotly. Learn design principles for effective charts.",
        "topics": ["data visualization", "python", "matplotlib", "charts", "data analysis"],
        "difficulty": "intermediate",
        "duration": "4 weeks",
        "format": "project-based",
        "rating": 4.4
    },
    {
        "id": "cybersecurity-basics",
        "title": "Cybersecurity Fundamentals",
        "description": "Introduction to cybersecurity concepts, threat analysis, and security best practices for developers and IT professionals.",
        "topics": ["cybersecurity", "security", "networking", "threats", "encryption"],
        "difficulty": "beginner",
        "duration": "6 weeks",
        "format": "theoretical",
        "rating": 4.3
    },
    {
        "id": "mobile-app-development",
        "title": "Mobile App Development with Flutter",
        "description": "Build cross-platform mobile applications using Flutter and Dart. Deploy to both iOS and Android stores.",
        "topics": ["mobile development", "flutter", "dart", "cross-platform", "apps"],
        "difficulty": "intermediate",
        "duration": "8 weeks",
        "format": "project-based",
        "rating": 4.5
    },
    {
        "id": "cloud-computing-aws",
        "title": "Cloud Computing with AWS",
        "description": "Learn Amazon Web Services fundamentals including EC2, S3, Lambda, and cloud architecture best practices.",
        "topics": ["cloud computing", "aws", "infrastructure", "serverless", "deployment"],
        "difficulty": "intermediate",
        "duration": "7 weeks",
        "format": "hands-on",
        "rating": 4.6
    },
    {
        "id": "ui-ux-design",
        "title": "UI/UX Design Principles",
        "description": "Master user interface and user experience design principles. Create wireframes, prototypes, and user-centered designs.",
        "topics": ["ui design", "ux design", "prototyping", "user research", "design thinking"],
        "difficulty": "beginner",
        "duration": "5 weeks",
        "format": "project-based",
        "rating": 4.4
    },
    {
        "id": "statistics-for-data-science",
        "title": "Statistics for Data Science",
        "description": "Essential statistics concepts for data analysis including hypothesis testing, regression, and probability distributions.",
        "topics": ["statistics", "data science", "hypothesis testing", "regression", "probability"],
        "difficulty": "intermediate",
        "duration": "6 weeks",
        "format": "theoretical",
        "rating": 4.2
    }
]

def init_database():
    """Initialize the database with sample data"""
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect("data/app.db")
    cursor = conn.cursor()
    
    try:
        # Create tables (same as in database.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                course_id VARCHAR(50),
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback_text TEXT,
                learning_style VARCHAR(50),
                difficulty_preference VARCHAR(20),
                pace_preference VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                course_id VARCHAR(50),
                interaction_type VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                preferred_topics TEXT,
                difficulty_level VARCHAR(20),
                learning_style VARCHAR(50),
                time_commitment VARCHAR(20),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id VARCHAR(50) PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                topics TEXT,
                difficulty VARCHAR(20),
                duration VARCHAR(50),
                format VARCHAR(50),
                rating REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample courses
        for course in SAMPLE_COURSES:
            cursor.execute("""
                INSERT OR REPLACE INTO courses 
                (id, title, description, topics, difficulty, duration, format, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course["id"],
                course["title"],
                course["description"],
                json.dumps(course["topics"]),
                course["difficulty"],
                course["duration"],
                course["format"],
                course["rating"]
            ))
        
        # Create a demo user
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, email) 
            VALUES (1, 'demo_user', 'demo@example.com')
        """)
        
        # Add some sample preferences for the demo user
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preferred_topics, difficulty_level, learning_style, time_commitment)
            VALUES (1, ?, 'beginner', 'hands-on', 'self-paced')
        """, (json.dumps(["python", "web development", "data science"]),))
        
        # Add some sample feedback
        sample_feedback = [
            (1, "python-fundamentals", 5, "Great course! Very clear explanations.", "hands-on", "beginner", "self-paced"),
            (1, "web-development-react", 4, "Good introduction to React, could use more examples.", "hands-on", "intermediate", "self-paced"),
            (1, "sql-database-design", 3, "Decent course but felt too theoretical.", "hands-on", "beginner", "self-paced")
        ]
        
        for feedback in sample_feedback:
            cursor.execute("""
                INSERT OR REPLACE INTO user_feedback 
                (user_id, course_id, rating, feedback_text, learning_style, difficulty_preference, pace_preference)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, feedback)
        
        # Add some sample interactions
        sample_interactions = [
            (1, "python-fundamentals", "completed"),
            (1, "web-development-react", "enrolled"),
            (1, "sql-database-design", "viewed")
        ]
        
        for interaction in sample_interactions:
            cursor.execute("""
                INSERT OR REPLACE INTO course_interactions 
                (user_id, course_id, interaction_type)
                VALUES (?, ?, ?)
            """, interaction)
        
        conn.commit()
        print(f"Successfully inserted {len(SAMPLE_COURSES)} sample courses")
        print("Created demo user with sample preferences and feedback")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_database() 