"""
App bridge: `App` class with static methods used by the UI.

All modification operations are dry-run by default (commit=False).
This ensures actions remain temporary unless the user explicitly
requests permanent changes.
"""

from __future__ import annotations

from typing import Dict, List, Any
import os
import uuid
import shutil
from core import classifier, file_operations, ai_classifier
from core.models import FileObject
from core.heuristics import HeuristicEngine
from core.database import Database

db = Database()

class App:
    """Backend interface for the UI (static methods)."""

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, object]:
        return classifier.classify_file(file_path)

    @staticmethod
    def list_files(directory: str | None = None) -> List[str]:
        return file_operations.list_files(directory)

    @staticmethod
    def move_file(src: str, dst: str, commit: bool = False, batch_id: str = None) -> Dict[str, object]:
        result = file_operations.move_file(src, dst, commit=commit)
        if commit and result.get("success") and batch_id:
            db.log_transaction(batch_id, src, dst)
        return result

    @staticmethod
    def rename_file(src: str, new_name: str, commit: bool = False) -> Dict[str, object]:
        return file_operations.rename_file(src, new_name, commit=commit)

    @staticmethod
    def delete_file(path: str, commit: bool = False) -> Dict[str, object]:
        return file_operations.delete_file(path, commit=commit)

    @staticmethod
    def type_sorter(directory: str) -> Dict[str, object]:
        out = {"directory": directory, "files": []}
        files = file_operations.list_files(directory)
        for name in files:
            full = os.path.join(directory, name)
            category, tags, suggested_folder, confidence = classifier.rule_based_classify(full)
            out["files"].append({
                "name": name,
                "category": category,
                "tags": tags,
                "suggested_folder": suggested_folder,
                "confidence": confidence,
                "source": "rule",
            })
        return out

    @staticmethod
    def ai_organize_folder(directory: str, progress_callback=None, cancel_event=None) -> Dict[str, Any]:
        """Run the new architecture AI pipeline."""
        if not os.path.exists(directory):
            return {"error": "Directory is not found."}

        if cancel_event and cancel_event.is_set():
            return {"error": "AI Scan cancelled.", "cancelled": True, "summary": "AI Scan cancelled by user.", "groups": []}

        if progress_callback: progress_callback(0, 1, "Deep scanning folder...")

        # 1. Crawler
        file_objects = []
        _id_counter = 1
        for root, dirs, files in os.walk(directory):
            if cancel_event and cancel_event.is_set():
                return {"error": "AI Scan cancelled.", "cancelled": True, "summary": "AI Scan cancelled by user.", "groups": []}

            for name in files:
                full = os.path.join(root, name)
                rel_path = os.path.relpath(full, directory)
                size = os.path.getsize(full) if os.path.exists(full) else 0
                _, ext = os.path.splitext(name)

                file_objects.append(FileObject(
                    id=_id_counter,
                    name=name,
                    ext=ext,
                    size=size,
                    original_path=rel_path
                ))
                _id_counter += 1

        if not file_objects:
            return {"error": "Directory is empty."}

        # Create an ID to Object map for fast lookup later
        id_map = {f.id: f for f in file_objects}

        # 2. Heuristics
        deterministic_groups, remaining_files = HeuristicEngine.extract_obvious_groups(file_objects)

        # We will build a unified JSON-like structure for the UI preview
        final_groups = []

        # Add deterministic groups
        for folder_name, files in deterministic_groups.items():
            final_groups.append({
                "folder_name": folder_name,
                "reason": "Rule-based heuristic matching",
                "confidence": 1.0,
                "files": [
                    {
                        "original_path": f.original_path,
                        "file_name": f.name
                    } for f in files
                ]
            })

        if cancel_event and cancel_event.is_set():
            return {"error": "AI Scan cancelled.", "cancelled": True, "summary": "AI Scan cancelled by user.", "groups": final_groups}

        # 3. AI Chunker and Processing
        if remaining_files:
            chunks = ai_classifier._chunk_files(remaining_files, chunk_size=25)
            total_chunks = len(chunks)
            for i, chunk in enumerate(chunks):
                if cancel_event and cancel_event.is_set():
                    return {"error": "AI Scan cancelled.", "cancelled": True, "summary": "AI Scan cancelled by user.", "groups": final_groups}

                if progress_callback:
                    progress_callback(i, total_chunks, f"AI processing batch {i+1} of {total_chunks}...")

                plan = ai_classifier.ai_organize_batch(chunk)

                # Remap the IDs back to files and append to final_groups
                for group in plan.groups:
                    group_files = []
                    for f_id in group.file_ids:
                        if f_id in id_map:
                            obj = id_map[f_id]
                            group_files.append({
                                "original_path": obj.original_path,
                                "file_name": obj.name
                            })
                    if group_files:
                        final_groups.append({
                            "folder_name": group.folder_name,
                            "reason": group.reason,
                            "confidence": group.confidence,
                            "files": group_files
                        })

        if progress_callback: progress_callback(1, 1, "Finalizing UI preview...")

        batch_id = str(uuid.uuid4())

        return {
            "summary": "Files organized successfully using heuristics and AI.",
            "groups": final_groups,
            "batch_id": batch_id
        }

    @staticmethod
    def undo_last_scan() -> Dict[str, Any]:
        """Undo the last batch of moves using SQLite logs."""
        transactions = db.get_latest_batch_transactions()
        if not transactions:
            return {"error": "No recent AI actions to undo."}
            
        batch_id = transactions[0][2]
        restored = 0
        failed = 0
        
        for original, target, _ in transactions:
            # We reverse it: src is target, dst is original
            if os.path.exists(target):
                os.makedirs(os.path.dirname(original), exist_ok=True)
                try:
                    shutil.move(target, original)
                    restored += 1
                except Exception:
                    failed += 1
                    
        db.mark_batch_rolled_back(batch_id)
        
        return {
            "success": True,
            "restored": restored,
            "failed": failed,
            "batch_id": batch_id
        }

if __name__ == "__main__":
    print("App bridge loaded.")
