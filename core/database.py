import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="smart_manager.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table to store classification history and confidence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_path TEXT UNIQUE,
                predicted_category TEXT,
                actual_category TEXT,
                source TEXT,      -- 'Rule-Based', 'AI', or 'Feedback'
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table to store user feedback for Level 3 Learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_extension TEXT,
                file_name_pattern TEXT,
                user_preferred_category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_classification(self, file_name, file_path, predicted, actual, source, confidence):
        """Save a classification event to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO classifications 
            (file_name, file_path, predicted_category, actual_category, source, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_name, file_path, predicted, actual, source, confidence))
        conn.commit()
        conn.close()

    def save_feedback(self, file_name, user_category):
        """Save user correction to teach the AI for future."""
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Simple feedback learning: mapping extension or partial name to category
        cursor.execute('''
            INSERT INTO feedback_rules (file_extension, file_name_pattern, user_preferred_category)
            VALUES (?, ?, ?)
        ''', (ext, file_name, user_category))
        conn.commit()
        conn.close()

    def get_feedback_rules(self):
        """Retrieve all learned feedback rules to inject into the AI prompt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_extension, file_name_pattern, user_preferred_category FROM feedback_rules')
        rules = cursor.fetchall()
        conn.close()
        return rules
