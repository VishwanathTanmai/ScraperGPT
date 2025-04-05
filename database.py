import sqlite3
import hashlib
import os
from datetime import datetime

# Database file
DB_FILE = "scrapegpt.db"

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def check_column_exists(table, column):
    """Check if a column exists in a table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query the table info to check if a column exists
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    
    conn.close()
    
    # Check if the column exists
    for col in columns:
        if col[1] == column:  # Column name is at index 1
            return True
    
    return False

def create_tables():
    """Create necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        profile_pic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create queries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Check if profile_pic column exists in users table, if not add it
    if not check_column_exists("users", "profile_pic"):
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
            print("Added profile_pic column to users table")
        except sqlite3.OperationalError as e:
            print(f"Error adding profile_pic column: {e}")
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Create a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def insert_user(username, email, password, profile_pic=None):
    """Insert a new user into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, profile_pic) VALUES (?, ?, ?, ?)",
        (username, email, password_hash, profile_pic)
    )
    
    conn.commit()
    conn.close()

def check_user_exists(email):
    """Check if a user with the given email exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    conn.close()
    
    return user is not None

def verify_user(email, password):
    """Verify user credentials and return user if valid."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    # Check if profile_pic column exists
    if check_column_exists("users", "profile_pic"):
        # If it exists, include it in the query
        cursor.execute(
            "SELECT id, username, profile_pic FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
    else:
        # If it doesn't exist, just query username and id
        cursor.execute(
            "SELECT id, username FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
    
    user = cursor.fetchone()
    
    conn.close()
    
    return user if user else None

def get_user_id(username):
    """Get user ID from username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    return user['id'] if user else None

def save_query(username, query):
    """Save a user query to the database."""
    user_id = get_user_id(username)
    if not user_id:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO queries (user_id, query) VALUES (?, ?)",
        (user_id, query)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_user_queries(username, limit=10):
    """Get recent queries for a user."""
    user_id = get_user_id(username)
    if not user_id:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, query, timestamp 
        FROM queries 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        """,
        (user_id, limit)
    )
    queries = cursor.fetchall()
    
    conn.close()
    
    return queries

def clear_user_queries(username):
    """Delete all queries for a specific user."""
    user_id = get_user_id(username)
    if not user_id:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM queries WHERE user_id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_user_profile_pic(username):
    """Get user's profile picture."""
    user_id = get_user_id(username)
    if not user_id:
        return None
    
    # Check if profile_pic column exists
    if not check_column_exists("users", "profile_pic"):
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT profile_pic FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result['profile_pic'] if result and result['profile_pic'] else None
    except sqlite3.OperationalError:
        conn.close()
        return None

def update_user_profile_pic(username, profile_pic):
    """Update a user's profile picture."""
    user_id = get_user_id(username)
    if not user_id:
        return False
    
    # Check if profile_pic column exists
    if not check_column_exists("users", "profile_pic"):
        # Try to add the column if it doesn't exist
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
            conn.commit()
            print("Added profile_pic column to users table")
        except sqlite3.OperationalError as e:
            print(f"Error adding profile_pic column: {e}")
            conn.close()
            return False
        conn.close()
    
    # Now try to update the profile pic
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET profile_pic = ? WHERE id = ?",
            (profile_pic, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return True
    except sqlite3.OperationalError as e:
        print(f"Error updating profile picture: {e}")
        conn.close()
        return False
