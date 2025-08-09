import sqlite3
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("data/app.db")

def get_db_connection():
    """Get a database connection"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    try:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User feedback and preferences
        conn.execute("""
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
        
        # Course interactions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS course_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                course_id VARCHAR(50),
                interaction_type VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences (derived from feedback)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                preferred_topics TEXT,
                difficulty_level VARCHAR(20),
                learning_style VARCHAR(50),
                time_commitment VARCHAR(20),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Courses table for basic course info
        conn.execute("""
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
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """Execute a query and return results"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        conn.commit()
        return result
    except Exception as e:
        logger.error(f"Database query error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_by_id(user_id: int):
    """Get user by ID"""
    return execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch_one=True)

def get_user_by_username(username: str):
    """Get user by username"""
    return execute_query("SELECT * FROM users WHERE username = ?", (username,), fetch_one=True) 