"""
Basic file operations with dry-run behavior by default.

All functions operate on the folder path provided by the UI.
The current UI folder is the selected/current folder, so the backend
uses that path directly. Write operations remain dry-run by default and
require `commit=True` to make permanent changes.
"""

from __future__ import annotations

import os
import shutil
from typing import List, Dict


def list_files(directory: str | None = None) -> List[str]:
	"""List files (non-recursive) in `directory` or current folder.

	Returns a list of file names in the selected directory.
	"""
	directory = directory or os.getcwd()
	directory = os.path.abspath(directory)

	if not os.path.isdir(directory):
		return []

	try:
		names = [n for n in os.listdir(directory) if os.path.isfile(os.path.join(directory, n))]
		return names
	except Exception:
		return []


def move_file(src: str, dst: str, commit: bool = False) -> Dict[str, object]:
	"""Move `src` -> `dst`.

	If `commit` is False the function performs a dry-run and does not
	modify the filesystem.
	"""
	src_abs = os.path.abspath(src)
	dst_abs = os.path.abspath(dst) if os.path.isabs(dst) else os.path.abspath(os.path.join(os.getcwd(), dst))

	result = {"action": "move", "src": src_abs, "dst": dst_abs, "commit": commit, "success": False, "message": ""}

	if not os.path.exists(src_abs):
		result["message"] = "Source does not exist"
		return result

	if not commit:
		result["success"] = True
		result["message"] = "Dry-run: move would succeed"
		return result

	try:
		os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
		shutil.move(src_abs, dst_abs)
		result["success"] = True
		result["message"] = "Moved"
	except Exception as e:
		result["message"] = str(e)

	return result


def rename_file(src: str, new_name: str, commit: bool = False) -> Dict[str, object]:
	"""Rename `src` to `new_name` (name or relative path).

	Dry-run behavior by default.
	"""
	src_abs = os.path.abspath(src)
	if os.path.isabs(new_name):
		dst_abs = os.path.abspath(new_name)
	else:
		dst_abs = os.path.abspath(os.path.join(os.path.dirname(src_abs), new_name))

	result = {"action": "rename", "src": src_abs, "dst": dst_abs, "commit": commit, "success": False, "message": ""}

	if not os.path.exists(src_abs):
		result["message"] = "Source does not exist"
		return result

	if not commit:
		result["success"] = True
		result["message"] = "Dry-run: rename would succeed"
		return result

	try:
		os.rename(src_abs, dst_abs)
		result["success"] = True
		result["message"] = "Renamed"
	except Exception as e:
		result["message"] = str(e)

	return result


def delete_file(path: str, commit: bool = False) -> Dict[str, object]:
	"""Delete a file at `path`. Dry-run by default."""
	path_abs = os.path.abspath(path)
	result = {"action": "delete", "path": path_abs, "commit": commit, "success": False, "message": ""}

	if not os.path.exists(path_abs):
		result["message"] = "Path does not exist"
		return result

	if not os.path.isfile(path_abs):
		result["message"] = "Path is not a file"
		return result

	if not commit:
		result["success"] = True
		result["message"] = "Dry-run: delete would succeed"
		return result

	try:
		os.remove(path_abs)
		result["success"] = True
		result["message"] = "Deleted"
	except Exception as e:
		result["message"] = str(e)

	return result


__all__ = ["list_files", "move_file", "rename_file", "delete_file"]

