import sqlite3
import time
from typing import List, Tuple

class Database:
    def __init__(self, db_path="smart_manager.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Original placeholder tables (if needed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_rules (
                id INTEGER PRIMARY KEY,
                file_extension TEXT,
                file_name_pattern TEXT,
                user_preferred_category TEXT
            )
        ''')

        # Classification history for future learning and debugging
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_path TEXT,
                predicted TEXT,
                actual TEXT,
                source TEXT,
                confidence REAL,
                timestamp REAL
            )
        ''')
        
        # New transaction logging table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS move_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                original_path TEXT,
                target_path TEXT,
                status TEXT,
                timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()

    def log_transaction(self, batch_id: str, original_path: str, target_path: str, status: str = "completed"):
        """Log a file move transaction for rollback capabilities."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO move_transactions (batch_id, original_path, target_path, status, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (batch_id, original_path, target_path, status, time.time()))
        conn.commit()
        conn.close()

    def get_latest_batch_transactions(self) -> List[Tuple[str, str, str]]:
        """Retrieve all completed transactions from the most recent batch."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get the latest batch_id
        cursor.execute('SELECT batch_id FROM move_transactions WHERE status = "completed" ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if not row:
            conn.close()
            return []
            
        batch_id = row[0]
        # Get all moves in that batch
        cursor.execute('SELECT original_path, target_path, batch_id FROM move_transactions WHERE batch_id = ? AND status = "completed"', (batch_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def mark_batch_rolled_back(self, batch_id: str):
        """Mark a batch as rolled back so it cannot be undone again."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE move_transactions SET status = "rolled_back" WHERE batch_id = ?', (batch_id,))
        conn.commit()
        conn.close()

    def save_classification(self, file_name, file_path, predicted, actual, source, confidence):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO classification_history (
                file_name, file_path, predicted, actual, source, confidence, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (file_name, file_path, predicted, actual, source, confidence, time.time()))
        conn.commit()
        conn.close()

    def get_classifications(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_name, file_path, predicted, actual, source, confidence, timestamp FROM classification_history ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_feedback_rules(self):
        """Retrieve all learned feedback rules to inject into the AI prompt."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT file_extension, file_name_pattern, user_preferred_category FROM feedback_rules')
            rules = cursor.fetchall()
            conn.close()
            return rules
        except sqlite3.OperationalError:
            return []
