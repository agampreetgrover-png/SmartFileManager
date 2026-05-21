import subprocess
import atexit
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
            
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
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
    app = MainWindow()
    app.mainloop()