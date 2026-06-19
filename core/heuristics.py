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
            path_parts = [p.lower() for p in file.original_path.split(os.sep)]

            # 1. Project/Git detection
            if ".git" in path_parts or "node_modules" in path_parts:
                deterministic_groups.setdefault("Code Projects Assets", []).append(file)
                continue

            # 2. Virtual Environments
            if "venv" in path_parts or ".env" in name or "pyproject.toml" in name or "requirements.txt" in name:
                deterministic_groups.setdefault("Project Configuration", []).append(file)
                continue

            # 3. Cache and Temps
            if ext in ['.tmp', '.cache', '.bak'] or '__pycache__' in file.original_path or 'thumbs.db' in name:
                deterministic_groups.setdefault("Temporary & Cache Files", []).append(file)
                continue

            # 4. OS Specific
            if name in ['.ds_store', 'thumbs.db', 'desktop.ini']:
                deterministic_groups.setdefault("OS System Files", []).append(file)
                continue

            # If no deterministic rule matched, send to AI
            remaining_files.append(file)
            
        return deterministic_groups, remaining_files
