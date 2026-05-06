import os
from core.classifier import SmartClassifier

class AppBridge:
    """Bridge between CustomTkinter UI and the Smart Classifier Backend"""
    def __init__(self):
        self.classifier = SmartClassifier(model_name="phi4-mini")

    def analyze_file(self, file_path):
        """Called when a user clicks 'AI' on a specific file"""
        if not os.path.exists(file_path):
            return {"error": "File not found"}
            
        result = self.classifier.process_and_save(file_path)
        return result

    def user_correction(self, file_path, correct_category):
        """Called when a user manually corrects an AI classification"""
        self.classifier.register_user_correction(file_path, correct_category)
        return {"status": "success", "message": f"Learned! Future files will be classified as {correct_category}"}
