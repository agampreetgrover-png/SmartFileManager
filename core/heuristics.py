import os
from typing import List, Dict, Tuple
from core.models import FileObject

class HeuristicEngine:
    @staticmethod
    def extract_obvious_groups(files: List[FileObject]) -> Tuple[Dict[str, List[FileObject]], List[FileObject]]:
        """
        Scans a list of FileObjects and deterministically extracts groups that are obvious.
        Returns:
            Tuple containing:
            - Dict of { "Folder Name": [List of FileObjects] }
            - List of remaining FileObjects that still need AI reasoning
        """
        deterministic_groups = {}
        remaining_files = []
        
        for file in files:
            ext = file.ext.lower()
            name = file.name.lower()
            
            # 1. Project/Git detection
            if ".git" in file.original_path.split(os.sep) or "node_modules" in file.original_path.split(os.sep):
                deterministic_groups.setdefault("Code Projects Assets", []).append(file)
                continue
                
            # 2. Virtual Environments
            if "venv" in file.original_path.split(os.sep) or ".env" in file.name:
                deterministic_groups.setdefault("Virtual Environments", []).append(file)
                continue
                
            # 3. Cache and Temps
            if ext in ['.tmp', '.cache', '.bak'] or '__pycache__' in file.original_path:
                deterministic_groups.setdefault("Temporary & Cache Files", []).append(file)
                continue
                
            # 4. OS Specific
            if file.name in ['.DS_Store', 'Thumbs.db', 'desktop.ini']:
                deterministic_groups.setdefault("OS System Files", []).append(file)
                continue
                
            # If no deterministic rule matched, send to AI
            remaining_files.append(file)
            
        return deterministic_groups, remaining_files
