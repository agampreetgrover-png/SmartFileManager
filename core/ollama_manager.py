"""
ollama_manager.py

Centralised interface for all Ollama operations:
- Health checking (is the Ollama service up?)
- Listing locally available models
- Pulling (downloading) a model with streamed progress
- Reading / writing the active model choice via config.json
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from collections import deque
from typing import Callable, Dict, List, Optional, Any

import requests

OLLAMA_BASE_URL = "http://localhost:11434"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
DEFAULT_MODEL = "phi4-mini"

# ──────────────────────────────────────────────
# PullStats type alias (passed to progress_cb)
# ──────────────────────────────────────────────
# {
#   "status":         str,   e.g. "pulling 3c168af1dea0"
#   "fraction":       float, 0.0 – 1.0  (-1.0 = unknown)
#   "completed_bytes":int,
#   "total_bytes":    int,
#   "speed_bps":      float, bytes per second  (0 = unknown)
#   "eta_seconds":    float, estimated seconds remaining  (-1 = unknown)
# }
PullStats = Dict[str, Any]


# ──────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────

def _load_config() -> dict:
    """Load config.json, returning defaults if missing."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"ollama_model": DEFAULT_MODEL}


def _save_config(data: dict) -> None:
    """Write config.json atomically."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ollama_manager] Failed to save config: {e}")


def get_active_model() -> str:
    """Return the currently configured model name."""
    return _load_config().get("ollama_model", DEFAULT_MODEL)


def set_active_model(model_name: str) -> None:
    """Persist the selected model to config.json."""
    cfg = _load_config()
    cfg["ollama_model"] = model_name
    _save_config(cfg)
    print(f"[ollama_manager] Active model set to: {model_name}")


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

def check_ollama_health() -> bool:
    """
    Return True if the Ollama service is reachable.
    Uses a fast HEAD / GET on the root endpoint.
    """
    try:
        r = requests.get(OLLAMA_BASE_URL, timeout=3)
        return r.status_code < 500
    except Exception:
        return False


# ──────────────────────────────────────────────
# Model listing
# ──────────────────────────────────────────────

def get_available_models() -> List[str]:
    """
    Return a list of model names that are already pulled locally.
    Queries the Ollama REST API (/api/tags).
    Falls back to an empty list on any error.
    """
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        data = r.json()
        models = [m["name"] for m in data.get("models", [])]
        return models
    except Exception as e:
        print(f"[ollama_manager] Could not fetch model list: {e}")
        return []


def is_model_available(model_name: str) -> bool:
    """Return True if model_name is already pulled locally."""
    available = get_available_models()
    # Match with or without the :latest tag
    base = model_name.split(":")[0]
    for m in available:
        if m == model_name or m.split(":")[0] == base:
            return True
    return False


# ──────────────────────────────────────────────
# Speed / ETA helpers
# ──────────────────────────────────────────────

class _SpeedTracker:
    """
    Rolling-window speed estimator.
    Keeps the last WINDOW (time, bytes) samples and computes bytes/sec
    over that window so the readout stays smooth but responsive.
    """
    WINDOW = 8  # number of samples to keep

    def __init__(self):
        self._samples: deque = deque(maxlen=self.WINDOW)

    def update(self, completed_bytes: int) -> float:
        """Record a new sample; return estimated bytes/sec (0 if insufficient data)."""
        now = time.monotonic()
        self._samples.append((now, completed_bytes))
        if len(self._samples) < 2:
            return 0.0
        t0, b0 = self._samples[0]
        t1, b1 = self._samples[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0
        return (b1 - b0) / dt

    def eta(self, completed_bytes: int, total_bytes: int, speed_bps: float) -> float:
        """Return estimated seconds to completion, or -1 if unknown."""
        if speed_bps <= 0 or total_bytes <= 0:
            return -1.0
        remaining = total_bytes - completed_bytes
        return remaining / speed_bps if remaining > 0 else 0.0


# ──────────────────────────────────────────────
# Model pulling
# ──────────────────────────────────────────────

def pull_model(
    model_name: str,
    progress_cb: Optional[Callable[[PullStats], None]] = None,
) -> bool:
    """
    Pull (download) a model via the Ollama REST streaming API.

    Args:
        model_name:  e.g. "phi4-mini"
        progress_cb: optional callback(stats: PullStats) called on every
                     progress event.  stats keys: status, fraction,
                     completed_bytes, total_bytes, speed_bps, eta_seconds.

    Returns:
        True on success, False on failure.
    """
    print(f"[ollama_manager] Pulling model: {model_name}")
    tracker = _SpeedTracker()

    def _make_stats(status: str, completed: int, total: int) -> PullStats:
        fraction = (completed / total) if total > 0 else -1.0
        speed = tracker.update(completed)
        eta = tracker.eta(completed, total, speed)
        return {
            "status": status,
            "fraction": fraction,
            "completed_bytes": completed,
            "total_bytes": total,
            "speed_bps": speed,
            "eta_seconds": eta,
        }

    # ── REST streaming pull ─────────────────────────────────────────────
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": model_name, "stream": True},
            stream=True,
            timeout=600,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                status    = obj.get("status", "")
                total     = obj.get("total", 0)
                completed = obj.get("completed", 0)

                if progress_cb:
                    progress_cb(_make_stats(status, completed, total))

                if status == "success":
                    print(f"[ollama_manager] Model {model_name} pulled successfully.")
                    return True

        return True  # stream ended without explicit 'success' — treat as OK

    except Exception as e:
        print(f"[ollama_manager] REST pull failed ({e}), falling back to CLI...")

    # ── CLI fallback ────────────────────────────────────────────────────
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            line = line.strip()
            if line and progress_cb:
                # CLI output has no byte counts — send a status-only stat
                progress_cb(_make_stats(line, 0, 0))
        proc.wait()
        success = proc.returncode == 0
        print(f"[ollama_manager] CLI pull {'succeeded' if success else f'failed (code {proc.returncode})'}.")
        return success
    except Exception as e:
        print(f"[ollama_manager] CLI pull also failed: {e}")
        return False


def pull_model_async(
    model_name: str,
    progress_cb: Optional[Callable[[PullStats], None]] = None,
    done_cb: Optional[Callable[[bool], None]] = None,
) -> threading.Thread:
    """
    Pull a model in a background thread.

    Args:
        model_name:  Model to pull.
        progress_cb: Called on the worker thread with PullStats on each event.
        done_cb:     Called on the worker thread with success=True/False when done.

    Returns:
        The started Thread (daemon=True).
    """
    def _worker():
        success = pull_model(model_name, progress_cb=progress_cb)
        if done_cb:
            done_cb(success)

    t = threading.Thread(target=_worker, daemon=True, name=f"ollama-pull-{model_name}")
    t.start()
    return t


# ──────────────────────────────────────────────
# Ensure model is ready (pull if needed)
# ──────────────────────────────────────────────

def ensure_model_ready(
    model_name: Optional[str] = None,
    progress_cb: Optional[Callable[[PullStats], None]] = None,
    done_cb: Optional[Callable[[bool], None]] = None,
) -> threading.Thread:
    """
    Check if model is available locally; pull it if not.
    Runs entirely in a background thread.

    Returns the started Thread.
    """
    if model_name is None:
        model_name = get_active_model()

    def _worker():
        if not check_ollama_health():
            print("[ollama_manager] Ollama service not reachable — skipping model check.")
            if done_cb:
                done_cb(False)
            return

        if is_model_available(model_name):
            print(f"[ollama_manager] Model {model_name} already available.")
            if progress_cb:
                progress_cb({
                    "status": "Model ready",
                    "fraction": 1.0,
                    "completed_bytes": 0,
                    "total_bytes": 0,
                    "speed_bps": 0.0,
                    "eta_seconds": 0.0,
                })
            if done_cb:
                done_cb(True)
            return

        print(f"[ollama_manager] Model {model_name} not found. Pulling...")
        success = pull_model(model_name, progress_cb=progress_cb)
        if done_cb:
            done_cb(success)

    t = threading.Thread(target=_worker, daemon=True, name="ollama-ensure-model")
    t.start()
    return t
