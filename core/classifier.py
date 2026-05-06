import os
import json
import requests
import subprocess
import time
from core.database import Database

class SmartClassifier:
    def __init__(self, ollama_url="http://localhost:11434/api/generate", model_name="llama3.2:3b"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.db = Database()
        self._ensure_ollama_running()
        
    def _ensure_ollama_running(self):
        """Silently start Ollama if it's not already running (for end-user convenience)."""
        try:
            # Check if Ollama API is already reachable
            requests.get("http://localhost:11434", timeout=1)
        except requests.ConnectionError:
            print("Ollama not detected. Starting background service...")
            try:
                # 0x08000000 is CREATE_NO_WINDOW on Windows. This prevents a black terminal box from flashing.
                subprocess.Popen(['ollama', 'serve'], creationflags=0x08000000)
                time.sleep(2) # Give it 2 seconds to boot up
            except Exception as e:
                print(f"Warning: Could not start Ollama automatically. {e}")
        
        # 1. Rule-based mappings (Fast fallback)
        self.extension_rules = {
            ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
            ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
            ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos",
            ".mp3": "Audio", ".wav": "Audio",
            ".zip": "Archives", ".rar": "Archives", ".tar": "Archives", ".gz": "Archives",
            ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code", ".cpp": "Code", ".java": "Code"
        }

    def read_file_preview(self, file_path, max_chars=1200):
        """Read the first few characters of a file for AI context (text files only)."""
        try:
            # Check if it's likely a text file before reading
            text_extensions = {".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".log"}
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() in text_extensions:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_chars)
                    return content.strip()
            return "Binary or non-text file content."
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _get_feedback_context(self):
        """Format past feedback rules into a string for the AI prompt."""
        rules = self.db.get_feedback_rules()
        if not rules:
            return "No user feedback history available yet."
            
        context = "USER FEEDBACK HISTORY (CRITICAL: Prioritize these rules if they apply):\n"
        for ext, pattern, category in rules[-10:]: # Use latest 10 rules to avoid prompt bloat
            context += f"- If file has extension '{ext}' or name matches '{pattern}', classify as '{category}'.\n"
        return context

    def classify_with_ai(self, file_name, file_content_preview):
        """Use local Ollama model to classify the file."""
        feedback_context = self._get_feedback_context()
        
        prompt = f"""You are an intelligent file organization assistant. Your job is to classify a file into a single directory category.
        
CATEGORIES: Documents, Images, Videos, Audio, Archives, Code, Setup, Work, Personal, Unknown.
(You can suggest a custom category if it fits perfectly based on User Feedback).

{feedback_context}

FILE DETAILS:
- File Name: {file_name}
- Content Snippet: {file_content_preview}

TASK:
Classify the file. Output ONLY a valid JSON object with exactly two keys: "category" and "confidence".
Example format:
{{"category": "Documents", "confidence": 0.95}}

Do not include any other text or markdown formatting.
"""
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json" # Forces Ollama to output valid JSON
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                parsed = json.loads(response_text)
                return parsed.get("category", "Unknown"), parsed.get("confidence", 0.0)
            else:
                return None, 0.0
        except Exception as e:
            print(f"AI Classification Error: {e}")
            return None, 0.0

    def classify_file(self, file_path):
        """Main classification pipeline."""
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()

        # Step 1: Check user feedback rules first (Level 3 Learning override)
        feedback_rules = self.db.get_feedback_rules()
        for rule_ext, rule_pattern, rule_category in reversed(feedback_rules):
            # Simple match logic
            if ext == rule_ext or (rule_pattern and rule_pattern in file_name):
                return {
                    "category": rule_category,
                    "confidence": 0.99,
                    "source": "Feedback Learning"
                }

        # Step 2: Try AI Classification
        content_preview = self.read_file_preview(file_path)
        ai_category, ai_confidence = self.classify_with_ai(file_name, content_preview)

        if ai_category and ai_category != "Unknown" and ai_confidence > 0.60:
            return {
                "category": ai_category,
                "confidence": ai_confidence,
                "source": "Ollama AI"
            }

        # Step 3: Fallback to Rule-based classification
        rule_category = self.extension_rules.get(ext, "Unknown")
        return {
            "category": rule_category,
            "confidence": 0.80 if rule_category != "Unknown" else 0.10,
            "source": "Rule-Based Fallback"
        }

    def process_and_save(self, file_path):
        """Classify file and save the result to the database."""
        file_name = os.path.basename(file_path)
        result = self.classify_file(file_path)
        
        self.db.save_classification(
            file_name=file_name,
            file_path=file_path,
            predicted=result["category"],
            actual=result["category"], # Assuming predicted is actual until user corrects
            source=result["source"],
            confidence=result["confidence"]
        )
        return result

    def register_user_correction(self, file_path, correct_category):
        """Handle user correcting the AI, creating a Level 3 learning loop."""
        file_name = os.path.basename(file_path)
        
        # Save rule to feedback table
        self.db.save_feedback(file_name, correct_category)
        
        # Update past classification record
        self.db.save_classification(
            file_name=file_name,
            file_path=file_path,
            predicted="corrected", 
            actual=correct_category,
            source="User Corrected",
            confidence=1.0
        )
