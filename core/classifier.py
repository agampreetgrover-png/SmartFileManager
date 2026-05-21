"""
Rule-based classifier (extension-only)

This module provides two functions used by the app backend:

- `rule_based_classify(file_path: str)` -> internal helper that returns
  a classification tuple based on file extension.
- `classify_file(file_path: str)` -> public function that returns a
  dictionary with the required keys: category, tags, suggested_folder,
  confidence, source.

Behavior and constraints:
- Classification is read-only and does NOT modify files or folders.
- Only classifies files that are inside the current working directory
  (the "current folder the user is in"). Files outside the current
  working directory are treated as out-of-scope and returned as
  category "Others" with confidence 0.0.
- Kept lightweight and easy to extend for future AI/feedback learning.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple


EXTENSION_MAP = {
    # Photos / Images
    "images": {"exts": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".webp"},
               "category": "Photos", "tags": ["image"], "suggested_folder": os.path.join("Media", "Photos")},

    # Videos
    "videos": {"exts": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"},
               "category": "Videos", "tags": ["video"], "suggested_folder": os.path.join("Media", "Videos")},

    # Audio / Music
    "audio": {"exts": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
              "category": "Music", "tags": ["audio"], "suggested_folder": os.path.join("Media", "Audio")},

    # Documents
    "documents": {"exts": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md"},
                  "category": "Documents", "tags": ["document"], "suggested_folder": "Documents"},

    # Code files
    "code": {"exts": {".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".c", ".cpp", ".h", ".cs", ".go", ".rb", ".php", ".rs", ".swift"},
             "category": "Code", "tags": ["code"], "suggested_folder": "Code"},

    # Archives
    "archives": {"exts": {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz"},
                 "category": "Archives", "tags": ["archive"], "suggested_folder": "Archives"},

    # Applications / executables
    "apps": {"exts": {".exe", ".msi", ".apk", ".dmg", ".AppImage"},
             "category": "Applications", "tags": ["executable"], "suggested_folder": "Applications"},
}


def rule_based_classify(file_path: str) -> Tuple[str, List[str], str, float]:
    """
    Classify a file using only its extension.

    Returns a tuple: (category, tags, suggested_folder, confidence)

    Confidence is a simple heuristic based on an exact extension match
    (high confidence) or fallback (low confidence).
    """

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if not ext:
        # No extension -> low confidence 'Others'
        return "Others", [], "", 0.25

    for bucket in EXTENSION_MAP.values():
        if ext in bucket["exts"]:
            # Strong match found
            # Use high confidence for clear extension matches
            return bucket["category"], bucket["tags"], bucket["suggested_folder"], 0.95

    # If extension not found in map, classify as Others with low confidence
    return "Others", [], "", 0.20


def _is_in_cwd(file_path: str) -> bool:
    """Return True if file_path is inside current working directory."""
    try:
        cwd = os.path.abspath(os.getcwd())
        target = os.path.abspath(file_path)
        # If file is the cwd itself allow it
        return os.path.commonpath([cwd, target]) == cwd
    except Exception:
        return False


def classify_file(file_path: str) -> Dict[str, object]:
    """
    Public API: classify a single file and return a dictionary.

    The returned dictionary has the shape:
    {
      "category": str,
      "tags": List[str],
      "suggested_folder": str,
      "confidence": float,
      "source": "rule"
    }

    Notes:
    - Classification is read-only and temporary; no files are moved.
    - Only classifies files inside the current working directory. Files
      outside that folder are treated as out-of-scope.
    """

    result: Dict[str, object] = {
        "category": "Others",
        "tags": [],
        "suggested_folder": "",
        "confidence": 0.0,
        "source": "rule",
    }

    # Basic validation: must be a file path
    if not os.path.exists(file_path):
        return result

    if os.path.isdir(file_path):
        return result

    # Only process files inside the current working directory
    if not _is_in_cwd(file_path):
        return result

    category, tags, suggested_folder, confidence = rule_based_classify(file_path)

    result.update({
        "category": category,
        "tags": tags,
        "suggested_folder": suggested_folder,
        "confidence": confidence,
    })

    return result


if __name__ == "__main__":
    # Simple CLI test: classify all files in the current folder (non-recursive)
    cwd = os.getcwd()
    print(f"Classifying files in current folder: {cwd}\n")
    for name in sorted(os.listdir(cwd)):
        path = os.path.join(cwd, name)
        if os.path.isfile(path):
            info = classify_file(path)
            print(f"{name}: {info}")

