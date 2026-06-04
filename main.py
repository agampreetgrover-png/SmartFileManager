import subprocess
import atexit
import time
from ui.main_window import MainWindow

ollama_process = None

def start_ollama():
    global ollama_process
    print("Starting Ollama service...")
    try:
        # Start ollama in the background, suppressing output
        # creationflags=subprocess.CREATE_NO_WINDOW prevents a console window from popping up on Windows
        creationflags = 0
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creationflags = subprocess.CREATE_NO_WINDOW
            
        try:
            ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
        except FileNotFoundError:
            # Fallback to standard installation paths on Windows
            import os
            candidates = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                r"C:\Program Files\Ollama\ollama.exe",
                r"C:\Program Files (x86)\Ollama\ollama.exe"
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    ollama_process = subprocess.Popen(
                        [candidate, "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags
                    )
                    print(f"Ollama started successfully from fallback path: {candidate}")
                    return
            raise FileNotFoundError()
    except FileNotFoundError:
        print("Warning: 'ollama' command not found. Ensure Ollama is installed and in your PATH.")
    except Exception as e:
        print(f"Failed to start Ollama: {e}")

def stop_ollama():
    global ollama_process
    if ollama_process:
        print("Stopping Ollama service...")
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_process.kill()

# Register the stop function to run when the program exits
atexit.register(stop_ollama)

if __name__ == "__main__":
    start_ollama()

    # Give the Ollama service a moment to be ready before the UI starts polling it
    time.sleep(1.5)

    app = MainWindow()

    # Kick off the model-readiness check in the background.
    # The MainWindow will update its status chip via after() callbacks.
    from core import ollama_manager
    ollama_manager.ensure_model_ready(
        progress_cb=lambda stats: app.on_ollama_pull_progress(stats),
        done_cb=lambda ok: app.on_ollama_ready(ok),
    )

    app.mainloop()