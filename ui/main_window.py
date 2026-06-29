import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.file_list import FileList
import threading
import time
import os
from app_bridge import App
from core import ollama_manager

MODEL_CAPABILITY_HINTS = {
    "phi4-mini:latest": "Compact, Fast",
    "phi4-small:latest": "Tiny, Very Fast",
    "phi4-medium:latest": "Balanced, Accurate",
    "phi4-large:latest": "Large, More Accurate",
    "llama2:replit": "General Purpose",
    "llama2:13b": "High Accuracy",
    "llama2:70b": "Very Large, Best Quality",
}

ctk.set_appearance_mode("light")  # Start with light mode
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart File Manager")
        self.geometry("1350x780")
        # Modern minimal backgrounds
        self.configure(fg_color=("#F8FAFC", "#0B0F19"))
        
        # Animation states
        self.ai_pulse_state = False

        # Ollama status tracking
        self._ollama_status = "offline"  # "offline" | "pulling" | "ready"
        self._pull_fraction = 0.0

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="ns", pady=0)
        
        # Main container that will hold Topbar, Path Breadcrumbs, FileList, and Statusbar
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")

        # Bridge to backend
        self.bridge = App
        self.ai_scan_cancel_event = threading.Event()
        self.ai_scan_thread = None
        self.scan_running = False
        self._active_scan_id = 0
        self._app_closing = False

        self.topbar = self.create_topbar()
        self.topbar.pack(in_=self.main_container, side="top", fill="x", pady=(16, 8), padx=16)

        self.breadcrumb_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.breadcrumb_frame.pack(in_=self.main_container, side="top", fill="x", padx=16, pady=(0, 8))
        self.path_label = ctk.CTkLabel(self.breadcrumb_frame, text=".", font=("Inter", 12, "bold"), text_color=("#6B7280", "#9CA3AF"))
        self.path_label.pack(anchor="w")

        self.file_list = FileList(self)
        self.file_list.pack(in_=self.main_container, side="top", fill="both", expand=True, padx=16, pady=(0, 8))

        # Create statusbar at the bottom
        self.statusbar = self.create_statusbar_panel()
        self.statusbar.pack(in_=self.main_container, side="bottom", fill="x", padx=16, pady=(0, 16))

        # Apply glass effect
        self.apply_glass_effect()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Schedule initial model refresh after the UI event loop begins
        self.after(100, self._refresh_model_list)

    def _safe_ui_call(self, callback):
        if self._app_closing or not self.winfo_exists():
            return
        try:
            self.after(0, callback)
        except Exception:
            pass

    def _set_scan_busy_state(self):
        self.ai_button.configure(state="disabled")
        self.type_sorter_btn.configure(state="disabled")
        self.cancel_scan_btn.configure(state="normal")
        self.cancel_scan_btn.pack(side="right", padx=(10, 0), pady=2)
        self.progress_bar.pack(side="right", padx=10, pady=2)
        self.progress_bar.set(0)

    def create_topbar(self):
        frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="transparent", border_width=0)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.pack(side="left", anchor="center")

        title_frame = ctk.CTkFrame(left, fg_color="transparent")
        title_frame.pack(anchor="w")

        title_1 = ctk.CTkLabel(title_frame, text="Smart ", font=("Inter", 32, "bold"), text_color=("#1F2937", "#F9FAFB"))
        title_1.pack(side="left")
        title_2 = ctk.CTkLabel(title_frame, text="File Manager", font=("Inter", 32, "bold"), text_color=("#6366F1", "#818CF8"))
        title_2.pack(side="left")

        subtitle = ctk.CTkLabel(left, text="Manage your files smarter with AI", font=("Inter", 14), text_color=("#6B7280", "#9CA3AF"))
        subtitle.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="right", anchor="center")

        # ── Ollama status chip ──────────────────────────────────────────
        self.ollama_chip = ctk.CTkFrame(
            right,
            height=32,
            corner_radius=16,
            fg_color=("#FEE2E2", "#450A0A"),   # starts red (offline)
            border_width=1,
            border_color=("#FCA5A5", "#7F1D1D"),
        )
        self.ollama_chip.pack(side="right", padx=(8, 0))

        self.ollama_dot = ctk.CTkLabel(
            self.ollama_chip,
            text="●",
            font=("Inter", 11),
            text_color=("#EF4444", "#F87171"),
        )
        self.ollama_dot.pack(side="left", padx=(10, 2), pady=4)

        self.ollama_chip_label = ctk.CTkLabel(
            self.ollama_chip,
            text="Ollama Offline",
            font=("Inter", 11, "bold"),
            text_color=("#B91C1C", "#FCA5A5"),
        )
        self.ollama_chip_label.pack(side="left", padx=(0, 10), pady=4)
        # ───────────────────────────────────────────────────────────────

        # AI Tools grouped section
        self.ai_tools_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.ai_tools_frame.pack(side="right", padx=8)

        self.ai_model_names = []
        self.ai_model_labels = []
        self.ai_model_map = {}

        self.undo_btn = ctk.CTkButton(
            self.ai_tools_frame,
            text="Undo Scan",
            width=85,
            height=32,
            corner_radius=8,
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            text_color="#FFFFFF",
            font=("Inter", 11, "bold"),
            command=self.run_undo_scan,
        )
        self.undo_btn.pack(side="right", padx=(4, 0))

        self.ai_button = ctk.CTkButton(
            self.ai_tools_frame,
            text="AI Scan",
            width=80,
            height=32,
            corner_radius=8,
            fg_color=("#6366F1", "#818CF8"),
            hover_color=("#818CF8", "#4F46E5"),
            text_color="#FFFFFF",
            font=("Inter", 11, "bold"),
            command=self.run_ai_scan,
            state="disabled"
        )
        self.ai_button.pack(side="right", padx=4)

        self.type_sorter_btn = ctk.CTkButton(
            self.ai_tools_frame,
            text="Type Sorter",
            width=95,
            height=32,
            corner_radius=8,
            fg_color=("#E5E7EB", "#111827"),
            hover_color=("#F3F4F6", "#374151"),
            text_color=("#1F2937", "#F9FAFB"),
            font=("Inter", 11, "bold"),
            command=self.run_type_sorter,
            state="disabled"
        )
        self.type_sorter_btn.pack(side="right", padx=(0, 4))

        # Browse Button
        self.browse_btn = ctk.CTkButton(
            right,
            text="📁 Browse",
            width=88,
            height=32,
            corner_radius=8,
            fg_color=("#FFFFFF", "#1F2937"),
            border_color=("#6366F1", "#818CF8"),
            border_width=1,
            hover_color=("#F3F4F6", "#374151"),
            text_color=("#6366F1", "#818CF8"),
            command=self.open_folder_dialog,
            font=("Inter", 12)
        )
        self.browse_btn.pack(side="right", padx=8)

        # Search Bar
        search = ctk.CTkEntry(
            right,
            width=180,
            height=32,
            corner_radius=16,
            placeholder_text="Search files...",
            fg_color=("#FFFFFF", "#1F2937"),
            border_color=("#E5E7EB", "#374151"),
            border_width=1,
            text_color=("#1F2937", "#F9FAFB"),
            font=("Inter", 12)
        )
        search.pack(side="right", padx=8)
        search.bind("<FocusIn>", lambda e: search.configure(border_color=("#6366F1", "#818CF8")))
        search.bind("<FocusOut>", lambda e: search.configure(border_color=("#E5E7EB", "#374151")))

        # Model Selector section
        model_section = ctk.CTkFrame(right, fg_color="transparent")
        model_section.pack(side="right", padx=8)

        ctk.CTkLabel(
            model_section,
            text="🤖",
            font=("Inter", 12),
        ).pack(side="left", padx=(0, 4))

        self._model_var = ctk.StringVar()
        self.model_selector = ctk.CTkOptionMenu(
            model_section,
            variable=self._model_var,
            values=[],
            width=200,
            height=32,
            corner_radius=8,
            fg_color=("#F3F4F6", "#111827"),
            button_color=("#E5E7EB", "#374151"),
            button_hover_color=("#D1D5DB", "#4B5563"),
            text_color=("#1F2937", "#F9FAFB"),
            font=("Inter", 11),
            dropdown_font=("Inter", 11),
            command=self._on_model_changed,
        )
        self.model_selector.pack(side="left")

        self.refresh_model_btn = ctk.CTkButton(
            model_section,
            text="↻",
            width=28,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=("#E5E7EB", "#374151"),
            hover_color=("#E5E7EB", "#374151"),
            text_color=("#6B7280", "#9CA3AF"),
            font=("Inter", 14),
            command=self._refresh_model_list,
        )
        self.refresh_model_btn.pack(side="left", padx=(4, 0))

        return frame
    
    def create_statusbar_panel(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")

        self.preview_msg = ctk.CTkLabel(
            frame, 
            text="No folder open.",
            font=("Inter", 11), 
            text_color=("#6B7280", "#9CA3AF"), 
            anchor="w",
            justify="left"
        )
        self.preview_msg.pack(side="left", anchor="center", pady=4)

        self.progress_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.progress_container.pack(side="right", anchor="center", fill="y")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_container, 
            width=180, 
            height=6, 
            corner_radius=3,
            progress_color=("#6366F1", "#818CF8")
        )
        self.progress_bar.set(0)

        self.cancel_scan_btn = ctk.CTkButton(
            self.progress_container,
            text="Cancel Scan",
            width=110,
            height=28,
            corner_radius=12,
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            text_color="#FFFFFF",
            font=("Inter", 10, "bold"),
            command=self.cancel_ai_scan
        )

        self.pull_bar = ctk.CTkProgressBar(
            self.progress_container, 
            width=150, 
            height=6, 
            corner_radius=3,
            progress_color=("#F59E0B", "#D97706"),
            fg_color=("#FEF3C7", "#292524")
        )
        self.pull_bar.set(0)

        self.pull_label = ctk.CTkLabel(
            self.progress_container,
            text="",
            font=("Inter", 11),
            text_color=("#92400E", "#FCD34D")
        )

        return frame

    # ── Model selector helpers ─────────────────────────────────────────────

    def _format_model_label(self, model_name: str) -> str:
        hint = MODEL_CAPABILITY_HINTS.get(model_name, "Standard")
        return f"{model_name} ({hint})"

    def _on_model_changed(self, display_label: str):
        """Called when user picks a different model."""
        model_name = self.ai_model_map.get(display_label, display_label)
        ollama_manager.set_active_model(model_name)
        self._model_var.set(display_label)
        self.preview_msg.configure(text=f"Model set to {model_name}")

    def _refresh_model_list(self):
        """Query Ollama for locally available models and update the dropdown."""
        def _fetch():
            models = ollama_manager.get_available_models()
            self._safe_ui_call(lambda: self._apply_model_list(models))

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_model_list(self, models):
        """Update model dropdown with fresh model list (must run on main thread)."""
        if not models:
            return
        current = ollama_manager.get_active_model()
        self.ai_model_names = models
        self.ai_model_labels = [self._format_model_label(model) for model in models]
        self.ai_model_map = {label: model for model, label in zip(models, self.ai_model_labels)}
        self.model_selector.configure(values=self.ai_model_labels)

        current = ollama_manager.get_active_model()
        if current in models:
            self._model_var.set(self._format_model_label(current))
        elif self.ai_model_labels:
            self._model_var.set(self.ai_model_labels[0])
            ollama_manager.set_active_model(self.ai_model_names[0])

    def open_folder_dialog(self):
        """Open a dialog to select a folder from the PC and load its files."""
        folder_path = ctk.filedialog.askdirectory(title="Select Folder to Manage")
        if folder_path:
            self.file_list.load_files(directory=folder_path, reset_root=True)

    def update_preview(self, name, full_path=None):
        # Extract filename by removing the emoji prefix if any
        display_name = name.split(" ", 1)[-1] if " " in name else name
        self.selected_file = full_path if full_path else display_name
        
        import time
        from datetime import datetime
        import os
        
        file_size = "-"
        file_date = "-"
        if full_path and os.path.exists(full_path):
            size = os.path.getsize(full_path)
            from ui.file_list import format_size
            file_size = format_size(size)
            mod_time = os.path.getmtime(full_path)
            file_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')

        # Update status when a file is selected
        self.preview_msg.configure(text=f"Selected: {display_name}")
        # Ensure type sorter is enabled when inside a folder
        if getattr(self.file_list, 'current_directory', None):
            self.type_sorter_btn.configure(state="normal")
        else:
            self.type_sorter_btn.configure(state="disabled")

    def get_theme_icon(self):
        return "☀️" if ctk.get_appearance_mode() == "Light" else "🌙"

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        # Update DWM dark mode attribute if running glass effect on Windows
        try:
            import platform
            import ctypes
            if platform.system() == "Windows":
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                is_dark = ctypes.c_int(1 if new_mode == "Dark" else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(is_dark),
                    ctypes.sizeof(is_dark)
                )
        except Exception:
            pass
        # Update all UI components with new colors
        self.after(100, self.refresh_ui_colors)

    def update_path_label(self, rel_path):
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()

        if rel_path is None:
            placeholder = ctk.CTkLabel(self.breadcrumb_frame, text=".", font=("Inter", 12, "bold"), text_color=("#6B7280", "#9CA3AF"))
            placeholder.pack(anchor="w")
            return

        root = os.path.basename(self.file_list.root_directory) or self.file_list.root_directory
        root_button = ctk.CTkButton(
            self.breadcrumb_frame,
            text=root,
            command=lambda p=self.file_list.root_directory: self.file_list.load_files(p),
            fg_color="transparent",
            hover_color=("#E5E7EB", "#374151"),
            text_color=("#6B7280", "#9CA3AF"),
            font=("Inter", 12, "bold"),
            width=1,
            height=24,
            corner_radius=0
        )
        root_button.pack(side="left")

        if rel_path != ".":
            path_so_far = self.file_list.root_directory
            for part in rel_path.split("/"):
                separator = ctk.CTkLabel(self.breadcrumb_frame, text=" / ", font=("Inter", 12), text_color=("#9CA3AF", "#93A7B0"))
                separator.pack(side="left")
                path_so_far = os.path.join(path_so_far, part)
                crumb = ctk.CTkButton(
                    self.breadcrumb_frame,
                    text=part,
                    command=lambda p=path_so_far: self.file_list.load_files(p),
                    fg_color="transparent",
                    hover_color=("#E5E7EB", "#374151"),
                    text_color=("#6B7280", "#9CA3AF"),
                    font=("Inter", 12),
                    width=1,
                    height=24,
                    corner_radius=0
                )
                crumb.pack(side="left")

    def go_to_parent(self):
        current = getattr(self.file_list, "current_directory", None)
        root = getattr(self.file_list, "root_directory", None)
        if not current or not root:
            return

        current_abs = os.path.abspath(current)
        root_abs = os.path.abspath(root)
        if current_abs == root_abs:
            return

        parent = os.path.dirname(current_abs)
        if parent.startswith(root_abs):
            self.file_list.load_files(parent)

    def refresh_ui_colors(self):
        """Refresh all UI colors for theme change"""
        # Since we use tuple colors, CTk handles the UI refresh automatically!
        if self.file_list.current_directory is None:
            self.file_list.show_welcome()
        else:
            self.file_list.load_files(directory=self.file_list.current_directory)
        self.sidebar.update_colors()

    # ── Ollama status chip callbacks ───────────────────────────────────────

    def _set_ollama_chip(self, status: str, label: str):
        """
        Update the topbar Ollama chip.
        status: "offline" | "pulling" | "ready"
        Must be called on the main thread.
        """
        self._ollama_status = status
        colors = {
            "offline": {
                "chip_fg":   ("#FEE2E2", "#450A0A"),
                "chip_bd":   ("#FCA5A5", "#7F1D1D"),
                "dot_color": ("#EF4444", "#F87171"),
                "txt_color": ("#B91C1C", "#FCA5A5"),
            },
            "pulling": {
                "chip_fg":   ("#FEF3C7", "#2D1F00"),
                "chip_bd":   ("#FCD34D", "#78350F"),
                "dot_color": ("#F59E0B", "#FCD34D"),
                "txt_color": ("#92400E", "#FCD34D"),
            },
            "ready": {
                "chip_fg":   ("#D1FAE5", "#052E16"),
                "chip_bd":   ("#6EE7B7", "#064E3B"),
                "dot_color": ("#10B981", "#34D399"),
                "txt_color": ("#065F46", "#6EE7B7"),
            },
        }
        c = colors.get(status, colors["offline"])
        try:
            self.ollama_chip.configure(fg_color=c["chip_fg"], border_color=c["chip_bd"])
            self.ollama_dot.configure(text_color=c["dot_color"])
            self.ollama_chip_label.configure(text=label, text_color=c["txt_color"])
        except Exception:
            pass

    # ── Formatting helpers ─────────────────────────────────────────────────

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        """Format a byte count as a human-readable string."""
        if n <= 0:
            return "0 B"
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    @staticmethod
    def _fmt_speed(bps: float) -> str:
        """Format bytes/sec as MB/s or KB/s."""
        if bps <= 0:
            return ""
        if bps >= 1_048_576:
            return f"{bps/1_048_576:.1f} MB/s"
        if bps >= 1024:
            return f"{bps/1024:.1f} KB/s"
        return f"{bps:.0f} B/s"

    @staticmethod
    def _fmt_eta(seconds: float) -> str:
        """Format ETA seconds as a compact human string."""
        if seconds < 0:
            return ""
        s = int(seconds)
        if s < 60:
            return f"{s}s"
        m, s = divmod(s, 60)
        if m < 60:
            return f"{m}m {s:02d}s"
        h, m = divmod(m, 60)
        return f"{h}h {m:02d}m"

    def on_ollama_pull_progress(self, stats: dict):
        """
        Called from background thread on each pull progress event.
        stats keys: status, fraction, completed_bytes, total_bytes,
                    speed_bps, eta_seconds
        """
        def _update():
            fraction       = stats.get("fraction", -1.0)
            completed      = stats.get("completed_bytes", 0)
            total          = stats.get("total_bytes", 0)
            speed          = stats.get("speed_bps", 0.0)
            eta            = stats.get("eta_seconds", -1.0)
            status_str     = stats.get("status", "")

            pct = int(fraction * 100) if fraction >= 0 else 0

            # ── Topbar chip: compact single-line
            speed_str = self._fmt_speed(speed)
            eta_str   = self._fmt_eta(eta)

            if total > 0:
                chip_parts = [f"📥 {pct}%"]
                if speed_str:
                    chip_parts.append(speed_str)
                if eta_str:
                    chip_parts.append(f"~{eta_str}")
                chip_text = "  ·  ".join(chip_parts)
            else:
                # status message with no bytes (manifest, verifying, etc.)
                short = status_str[:28] + "…" if len(status_str) > 28 else status_str
                chip_text = f"⬇ {short}" if short else "Pulling model…"

            self._set_ollama_chip("pulling", chip_text)

            # ── Status bar: progress bar + detail line
            try:
                self.pull_bar.pack(side="right", padx=10, pady=2)
                self.pull_label.pack(side="right", padx=10, pady=2)

                if total > 0:
                    done_str  = self._fmt_bytes(completed)
                    total_str = self._fmt_bytes(total)
                    detail    = f"{done_str} / {total_str}"
                    if speed_str:
                        detail += f"   •   {speed_str}"
                    if eta_str:
                        detail += f"   •   ~{eta_str} left"
                    self.pull_label.configure(text=detail)
                    self.pull_bar.set(max(0.0, min(1.0, fraction)))
                else:
                    self.pull_label.configure(text=status_str[:70])
                    self.pull_bar.set(0)

            except Exception:
                pass

        self.after(0, _update)

    def on_ollama_ready(self, success: bool):
        """
        Called from background thread when ensure_model_ready() finishes.
        Schedules UI update on main thread.
        """
        def _update():
            if success:
                self._set_ollama_chip("ready", "Ollama Ready")
                # Refresh model list in selector
                self._refresh_model_list()
            else:
                self._set_ollama_chip("offline", "Ollama Offline")
            # Hide pull progress
            try:
                self.pull_bar.pack_forget()
                self.pull_label.pack_forget()
            except Exception:
                pass
        self.after(0, _update)

    def on_folder_changed(self):
        # Called by FileList when the current folder changes
        directory = getattr(self.file_list, 'current_directory', None)
        if directory:
            try:
                self.type_sorter_btn.configure(state="normal")
                self.ai_button.configure(state="normal")
                self.preview_msg.configure(text=f"Folder open: {os.path.basename(directory) or directory}")
            except Exception:
                pass
        else:
            try:
                self.type_sorter_btn.configure(state="disabled")
                self.ai_button.configure(state="disabled")
                self.preview_msg.configure(text="No folder open.")
            except Exception:
                pass

    def run_type_sorter(self):
        # Run rule-based classification across current directory
        directory = getattr(self.file_list, 'current_directory', None)
        if not directory:
            self.preview_msg.configure(text="No folder open for Type Sorter.")
            return

        summary = self.bridge.type_sorter(directory)
        files = summary.get('files', [])

        win = ctk.CTkToplevel(self)
        win.transient(self)
        win.grab_set()
        win.focus_force()
        win.geometry("520x460")
        win.title("Type Sorter Preview")
        win.configure(fg_color=("#F3F4F6", "#071E22"))

        header = ctk.CTkLabel(win, text=f"Type Sorter — {os.path.basename(directory)}", font=("Inter", 15, "bold"))
        header.pack(pady=(12, 4))

        note = ctk.CTkLabel(win, text="Preview only: no files are moved until you confirm.", font=("Inter", 11), text_color=("#4B5563", "#9CA3AF"))
        note.pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(win, fg_color=("#FFFFFF", "#1F2937"), border_width=1, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        if not files:
            ctk.CTkLabel(scroll, text="No files found in this folder.", font=("Inter", 12), text_color=("#111827", "#F9FAFB")).pack(pady=20)
        else:
            grouped = {}
            for item in files:
                group = item.get('suggested_folder') or item.get('category') or 'Others'
                grouped.setdefault(group, []).append(item.get('name', ''))

            for group_name, file_names in sorted(grouped.items()):
                section = ctk.CTkFrame(scroll, fg_color=("#F3F4F6", "#111827"), corner_radius=10)
                section.pack(fill="x", padx=10, pady=8)

                title = ctk.CTkLabel(section, text=f"{group_name} ({len(file_names)})", font=("Inter", 12, "bold"), anchor="w")
                title.pack(fill="x", padx=12, pady=(10, 4))

                body = ctk.CTkFrame(section, fg_color=("#FFFFFF", "#111827"), corner_radius=8)
                body.pack(fill="x", padx=12, pady=(0, 10))

                for file_name in file_names:
                    item_row = ctk.CTkFrame(body, fg_color=("#F9FAFB", "#1F2937"), corner_radius=6)
                    item_row.pack(fill="x", padx=6, pady=4)
                    ctk.CTkLabel(item_row, text=file_name, font=("Inter", 10), anchor="w").pack(fill="x", padx=10, pady=6)

        buttons = ctk.CTkFrame(win, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        undo_btn = ctk.CTkButton(buttons, text="Undo", width=100, height=32, corner_radius=8, fg_color=("#E5E7EB", "#374151"), text_color=("#1F2937", "#F9FAFB"), command=win.destroy)
        undo_btn.pack(side="left", padx=(0, 8))

        go_btn = ctk.CTkButton(buttons, text="Go On", width=100, height=32, corner_radius=8, fg_color=("#10B981", "#065F46"), hover_color=("#059669", "#047857"), text_color="#FFFFFF", command=lambda: confirm_type_sorter())
        go_btn.pack(side="right")

        def confirm_type_sorter():
            confirm = ctk.CTkToplevel(self)
            confirm.transient(win)
            confirm.grab_set()
            confirm.focus_force()
            confirm.geometry("360x180")
            confirm.title("Confirm Type Sorter")
            confirm.configure(fg_color=("#F3F4F6", "#071E22"))

            ctk.CTkLabel(confirm, text="Are you sure?", font=("Inter", 15, "bold")).pack(pady=(20, 6))
            ctk.CTkLabel(confirm, text="This will permanently move files to suggested folders.", font=("Inter", 11), text_color=("#4B5563", "#9CA3AF"), wraplength=320, justify="center").pack(pady=(0, 16))

            action_frame = ctk.CTkFrame(confirm, fg_color="transparent")
            action_frame.pack(pady=10)

            cancel_btn = ctk.CTkButton(action_frame, text="Cancel", width=100, height=32, corner_radius=8, fg_color=("#E5E7EB", "#374151"), text_color=("#1F2937", "#F9FAFB"), command=confirm.destroy)
            cancel_btn.pack(side="left", padx=8)

            def apply_type_sorter():
                confirm.destroy()
                win.destroy()
                moves = []
                for item in files:
                    if not item.get('suggested_folder'):
                        continue
                    src = os.path.join(directory, item['name'])
                    dst_dir = os.path.join(directory, item['suggested_folder'])
                    dst = os.path.join(dst_dir, item['name'])
                    if os.path.exists(src) and os.path.isfile(src):
                        result = self.bridge.move_file(src, dst, commit=True)
                        moves.append((item['name'], result))

                self.file_list.load_files(directory)
                summary_text = f"Moved {sum(1 for _, r in moves if r.get('success'))} files."
                self.preview_msg.configure(text=summary_text)

            confirm_btn = ctk.CTkButton(action_frame, text="Confirm", width=100, height=32, corner_radius=8, fg_color=("#2563EB", "#1D4ED8"), hover_color=("#1E40AF", "#1D4ED8"), text_color="#FFFFFF", command=apply_type_sorter)
            confirm_btn.pack(side="left", padx=8)

    def run_ai_scan(self):
        directory = getattr(self.file_list, 'current_directory', None)
        if not directory:
            self.preview_msg.configure(text="No folder open for AI Scan.")
            return

        if self.scan_running:
            self.preview_msg.configure(text="AI Scan already running.")
            return

        self._active_scan_id += 1
        run_id = self._active_scan_id
        cancel_event = threading.Event()
        self.ai_scan_cancel_event = cancel_event

        self.preview_msg.configure(text="Starting AI Scan...")
        self._set_scan_busy_state()
        self.scan_running = True

        def update_progress(current, total, msg):
            self._safe_ui_call(lambda: self._update_progress_ui(current, total, msg))

        def background_task():
            try:
                result = self.bridge.ai_organize_folder(
                    directory,
                    progress_callback=update_progress,
                    cancel_event=cancel_event
                )
            except Exception as e:
                result = {"error": str(e)}
            self._safe_ui_call(lambda: self._on_ai_scan_complete(directory, result, run_id))

        self.ai_scan_thread = threading.Thread(target=background_task, daemon=True)
        self.ai_scan_thread.start()

    def _update_progress_ui(self, current, total, msg):
        self.preview_msg.configure(text=msg)
        if total > 0:
            self.progress_bar.set(current / total)
        else:
            self.progress_bar.set(0)

    def cancel_ai_scan(self):
        if not self.scan_running:
            return

        if hasattr(self, 'ai_scan_cancel_event'):
            self.ai_scan_cancel_event.set()
        self.preview_msg.configure(text="AI Scan cancelled.")
        self.cancel_scan_btn.configure(state="disabled")
        self._end_ai_scan()

    def _end_ai_scan(self, message=None):
        self.scan_running = False
        try:
            self.progress_bar.set(0)
            self.progress_bar.pack_forget()
        except Exception:
            pass
        try:
            self.cancel_scan_btn.configure(state="normal")
            self.cancel_scan_btn.pack_forget()
        except Exception:
            pass
        try:
            self.on_folder_changed()
        except Exception:
            pass
        if message is not None:
            self.preview_msg.configure(text=message)

    def _on_ai_scan_complete(self, directory, result, run_id=None):
        if run_id is not None and run_id != self._active_scan_id:
            return

        self._end_ai_scan()
        if result.get("cancelled"):
            self.preview_msg.configure(text="AI Scan cancelled.")
            return

        if "error" in result:
            self.preview_msg.configure(text=f"AI Error: {result['error']}")
            return

        self.preview_msg.configure(text="AI Scan complete!")
        self.show_ai_scan_preview(directory, result)

    def _on_close(self):
        self._app_closing = True
        if self.scan_running and hasattr(self, 'ai_scan_cancel_event'):
            self.ai_scan_cancel_event.set()
        self.destroy()

    def run_undo_scan(self):
        result = self.bridge.undo_last_scan()
        if "error" in result:
            self.preview_msg.configure(text=result["error"])
        else:
            r = result.get("restored", 0)
            f = result.get("failed", 0)
            self.preview_msg.configure(text=f"Undo complete: {r} restored, {f} failed.")
            if getattr(self.file_list, 'current_directory', None):
                self.file_list.load_files(self.file_list.current_directory)

    def show_ai_scan_preview(self, directory, result):
        win = ctk.CTkToplevel(self)
        win.transient(self)
        win.grab_set()
        win.focus_force()
        win.geometry("1000x750")
        win.resizable(True, True)
        win.title("AI Organizer Preview")
        win.configure(fg_color=("#F3F4F6", "#071E22"))

        summary = result.get('summary', 'AI successfully organized your files.')
        header = ctk.CTkLabel(win, text="AI Organizer Recommendations", font=("Inter", 16, "bold"))
        header.pack(pady=(12, 4))
        
        note = ctk.CTkLabel(win, text=summary, font=("Inter", 11), text_color=("#4B5563", "#9CA3AF"), wraplength=550)
        note.pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(win, fg_color=("#FFFFFF", "#1F2937"), border_width=1, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        groups = result.get('groups', [])
        batch_id = result.get('batch_id')

        selected_items = set()
        drag_state = {
            "active": False,
            "source_group": None,
        }
        group_ui = []

        def _refresh_selection_styles():
            for gi, ui in enumerate(group_ui):
                for fi, item_frame in enumerate(ui.get("item_frames", [])):
                    if (gi, fi) in selected_items:
                        item_frame.configure(fg_color=("#DBEAFE", "#1E3A8A"), border_color=("#93C5FD", "#60A5FA"))
                    else:
                        item_frame.configure(fg_color=("#F9FAFB", "#1F2937"), border_color=("#E5E7EB", "#374151"))

        def _clear_highlights():
            for ui in group_ui:
                ui["frame"].configure(border_color=("#E5E7EB", "#374151"), fg_color=("#F3F4F6", "#111827"))

        def _highlight_group(gi, entering):
            if not drag_state["active"]:
                return
            ui = group_ui[gi]
            if entering:
                ui["frame"].configure(border_color=("#8B5CF6", "#7C3AED"), fg_color=("#EEF2FF", "#1E293B"))
            else:
                ui["frame"].configure(border_color=("#E5E7EB", "#374151"), fg_color=("#F3F4F6", "#111827"))

        def _select_file(gi, fi, add=False):
            key = (gi, fi)
            if add:
                if key in selected_items:
                    selected_items.remove(key)
                else:
                    selected_items.add(key)
            else:
                selected_items.clear()
                selected_items.add(key)
            _refresh_selection_styles()

        def _start_drag(gi):
            drag_state["active"] = True
            drag_state["source_group"] = gi

        def _drop_to_group(target_gi):
            if not drag_state["active"]:
                return
            if drag_state["source_group"] is None:
                drag_state["active"] = False
                return
            if target_gi == drag_state["source_group"]:
                drag_state["active"] = False
                _clear_highlights()
                return

            transfer = sorted(selected_items, reverse=True)
            if not transfer:
                drag_state["active"] = False
                _clear_highlights()
                return

            moved = []
            for gi, fi in transfer:
                if gi < 0 or gi >= len(groups):
                    continue
                source_files = groups[gi].get("files", [])
                if fi < 0 or fi >= len(source_files):
                    continue
                moved.append(source_files.pop(fi))

            groups[target_gi].setdefault("files", []).extend(reversed(moved))
            selected_items.clear()
            drag_state["active"] = False
            _clear_highlights()
            _render_groups()

        def _prompt_group_rename(gi):
            group = groups[gi]
            edit_win = ctk.CTkToplevel(win)
            edit_win.transient(win)
            edit_win.grab_set()
            edit_win.title("Rename Suggested Folder")
            edit_win.geometry("420x140")
            edit_win.configure(fg_color=("#F3F4F6", "#071E22"))

            ctk.CTkLabel(edit_win, text="Folder Name", font=("Inter", 13, "bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 4))
            name_var = ctk.StringVar(value=group.get("folder_name", ""))
            name_entry = ctk.CTkEntry(edit_win, textvariable=name_var, width=380, height=36, corner_radius=12)
            name_entry.pack(padx=16, pady=(0, 12))
            name_entry.focus()

            button_row = ctk.CTkFrame(edit_win, fg_color="transparent")
            button_row.pack(fill="x", padx=16, pady=(0, 12))

            def _save_name():
                new_name = name_var.get().strip()
                if new_name:
                    group["folder_name"] = new_name
                    _render_groups()
                edit_win.destroy()

            ctk.CTkButton(button_row, text="Cancel", width=120, height=32, corner_radius=10, fg_color=("#E5E7EB", "#374151"), text_color=("#1F2937", "#F9FAFB"), command=edit_win.destroy).pack(side="left")
            ctk.CTkButton(button_row, text="Save", width=120, height=32, corner_radius=10, fg_color=("#2563EB", "#1D4ED8"), text_color="#FFFFFF", command=_save_name).pack(side="right")

        def _render_groups():
            for widget in scroll.winfo_children():
                widget.destroy()

            instruction = ctk.CTkLabel(scroll, text="Drag files into another suggested folder to relocate them. Ctrl+click to select multiple files.", font=("Inter", 11), text_color=("#D1D5DB", "#CBD5E1"), wraplength=940, justify="left")
            instruction.pack(fill="x", padx=10, pady=(10, 8))
            group_ui.clear()

            if not groups:
                ctk.CTkLabel(scroll, text="No files were organized.", font=("Inter", 12), text_color=("#111827", "#F9FAFB")).pack(pady=20)
                return

            for gi, group in enumerate(groups):
                group_name = group.get('folder_name', 'Unknown Folder')
                files = group.get('files', [])
                reason = group.get('reason', 'No reason provided')
                confidence = group.get('confidence', 0.0)

                section = ctk.CTkFrame(scroll, fg_color=("#F3F4F6", "#111827"), corner_radius=10, border_width=1, border_color=("#E5E7EB", "#374151"))
                section.pack(fill="x", padx=10, pady=8)

                header = ctk.CTkFrame(section, fg_color="transparent")
                header.pack(fill="x", padx=12, pady=(10, 4))

                title_label = ctk.CTkLabel(header, text=f"{group_name} ({len(files)})", font=("Inter", 12, "bold"), anchor="w")
                title_label.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(header, text=f"{len(files)} files", font=("Inter", 10), text_color=("#6B7280", "#9CA3AF"), fg_color="transparent").pack(side="right", padx=(0, 8))
                ctk.CTkButton(header, text="Rename", width=90, height=28, corner_radius=10, fg_color=("#E5E7EB", "#374151"), text_color=("#1F2937", "#F9FAFB"), command=lambda gi=gi: _prompt_group_rename(gi)).pack(side="right")

                subtitle = ctk.CTkLabel(
                    section,
                    text=f"{reason} · Confidence: {int(confidence * 100)}%",
                    font=("Inter", 10),
                    text_color=("#6B7280", "#9CA3AF"),
                    anchor="w",
                    wraplength=860,
                    justify="left"
                )
                subtitle.pack(fill="x", padx=12, pady=(0, 8))

                body = ctk.CTkFrame(section, fg_color=("#FFFFFF", "#111827"), corner_radius=8, border_width=1, border_color=("#E5E7EB", "#374151"))
                body.pack(fill="x", padx=12, pady=(0, 10))

                def _bind_drop_zone(widget, gi=gi):
                    widget.bind("<Enter>", lambda e: _highlight_group(gi, True))
                    widget.bind("<Leave>", lambda e: _highlight_group(gi, False))
                    widget.bind("<ButtonRelease-1>", lambda e: _drop_to_group(gi))

                _bind_drop_zone(section)
                _bind_drop_zone(body)

                ui_data = {
                    "frame": section,
                    "item_frames": []
                }

                for fi, item in enumerate(files):
                    item_row = ctk.CTkFrame(body, fg_color=("#F9FAFB", "#1F2937"), corner_radius=6, border_width=1, border_color=("#E5E7EB", "#374151"))
                    item_row.pack(fill="x", padx=6, pady=4)
                    ui_data["item_frames"].append(item_row)

                    file_name = item.get('file_name', 'Unknown')
                    original = item.get('original_path', file_name)
                    label_text = f"{original}"

                    ctk.CTkLabel(
                        item_row,
                        text=label_text,
                        font=("Inter", 10),
                        justify="left",
                        anchor="w",
                        wraplength=860
                    ).pack(fill="x", padx=10, pady=6)

                    def _on_item_press(event, gi=gi, fi=fi):
                        add = (event.state & 0x4) != 0
                        _select_file(gi, fi, add=add)
                        _start_drag(gi)

                    item_row.bind("<Button-1>", _on_item_press)
                    item_row.bind("<B1-Motion>", lambda e, gi=gi: _start_drag(gi))

                group_ui.append(ui_data)

        _render_groups()

        buttons = ctk.CTkFrame(win, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        undo_btn = ctk.CTkButton(buttons, text="Cancel", width=100, height=32, corner_radius=8, fg_color=("#E5E7EB", "#374151"), text_color=("#1F2937", "#F9FAFB"), command=win.destroy)
        undo_btn.pack(side="left", padx=(0, 8))

        go_btn = ctk.CTkButton(buttons, text="Apply Recommendations", width=160, height=32, corner_radius=8, fg_color=("#8B5CF6", "#6D28D9"), hover_color=("#7C3AED", "#5B21B6"), text_color="#FFFFFF", command=lambda: apply_ai_scan())
        go_btn.pack(side="right")

        def apply_ai_scan():
            win.destroy()
            moves = 0
            for group in groups:
                folder_name = group.get('folder_name')
                if not folder_name: continue
                
                for item in group.get('files', []):
                    original = item.get('original_path')
                    file_name = item.get('file_name')
                    if not original or not file_name: continue
                    
                    src = os.path.join(directory, original)
                    dst_dir = os.path.join(directory, folder_name)
                    dst = os.path.join(dst_dir, file_name)
                    
                    if os.path.exists(src) and os.path.isfile(src):
                        os.makedirs(dst_dir, exist_ok=True)
                        res = self.bridge.move_file(src, dst, commit=True, batch_id=batch_id)
                        if res.get('success'): moves += 1

            self.file_list.load_files(directory)
            summary_text = f"AI applied! Moved {moves} files. Undo available."
            self.preview_msg.configure(text=summary_text)

    def apply_glass_effect(self):
        """
        Applies immersive dark mode titlebar settings to the window on Windows.
        """
        import platform
        import ctypes
        
        if platform.system() != "Windows":
            return
            
        try:
            self.update()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()
                
            # Set immersive dark mode titlebar attribute
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            is_dark = ctypes.c_int(1 if ctk.get_appearance_mode() == "Dark" else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(is_dark),
                ctypes.sizeof(is_dark)
            )
        except Exception as e:
            print(f"Failed to set immersive theme: {e}")