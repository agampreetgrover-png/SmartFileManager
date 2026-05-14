# Database - SQLite persistence layer (placeholder for future implementation)

class Database:
    def __init__(self, db_path="smart_manager.db"):
        self.db_path = db_path

    def save_classification(self, file_name, file_path, predicted, actual, source, confidence):
        pass

    def get_classifications(self):
        return []

    def get_feedback_rules(self):
        """Retrieve all learned feedback rules to inject into the AI prompt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_extension, file_name_pattern, user_preferred_category FROM feedback_rules')
        rules = cursor.fetchall()
        conn.close()
        return rules
