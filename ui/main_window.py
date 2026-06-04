import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.file_list import FileList
import threading
import time
import os
from app_bridge import App
from core import ollama_manager

ctk.set_appearance_mode("light")  # Start with light mode
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart File Manager")
        self.geometry("1350x780")
        # Modern minimal backgrounds
        self.configure(fg_color=("#F5F5F5", "#111827"))
        
        # Animation states
        self.ai_pulse_state = False

        # Ollama status tracking
        self._ollama_status = "offline"  # "offline" | "pulling" | "ready"
        self._pull_fraction = 0.0

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="ns", pady=0)
        
        self.topbar = self.create_topbar()
        self.topbar.grid(row=0, column=1, columnspan=2, sticky="ew")

        self.file_list = FileList(self)
        self.file_list.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))

        # Bridge to backend
        self.bridge = App

        self.preview = self.create_preview_panel()
        self.preview.grid(row=1, column=2, sticky="nsew", padx=(0, 20), pady=(0, 20))

    def create_topbar(self):
        frame = ctk.CTkFrame(self, height=100, corner_radius=0, fg_color="transparent", border_width=0)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.pack(side="left", padx=30, pady=20)

        title_frame = ctk.CTkFrame(left, fg_color="transparent")
        title_frame.pack(anchor="w")

        title_1 = ctk.CTkLabel(title_frame, text="Smart ", font=("Inter", 22, "bold"), text_color=("#1F2937", "#F9FAFB"))
        title_1.pack(side="left")
        title_2 = ctk.CTkLabel(title_frame, text="File Manager", font=("Inter", 22, "bold"), text_color=("#6366F1", "#818CF8"))
        title_2.pack(side="left")

        subtitle = ctk.CTkLabel(left, text="Manage your files smarter with AI", font=("Inter", 13), text_color=("#6B7280", "#9CA3AF"))
        subtitle.pack(anchor="w", pady=(2, 0))

        self.breadcrumb_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.breadcrumb_frame.pack(anchor="w", pady=(6, 0))
        self.path_label = ctk.CTkLabel(self.breadcrumb_frame, text=".", font=("Inter", 12, "bold"), text_color=("#6B7280", "#9CA3AF"))
        self.path_label.pack(anchor="w")

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="right", padx=10, pady=20)

        self.theme_btn = ctk.CTkButton(
            right,
            text=self.get_theme_icon(),
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            border_width=1,
            border_color=("#E5E7EB", "#374151"),
            hover_color=("#E5E7EB", "#374151"),
            text_color=("#111827", "#F9FAFB"),
            font=("Inter", 16),
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right", padx=10)

        # ── Ollama status chip ──────────────────────────────────────────
        self.ollama_chip = ctk.CTkFrame(
            right,
            height=30,
            corner_radius=15,
            fg_color=("#FEE2E2", "#450A0A"),   # starts red (offline)
            border_width=1,
            border_color=("#FCA5A5", "#7F1D1D"),
        )
        self.ollama_chip.pack(side="right", padx=10)

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

        search = ctk.CTkEntry(right, width=220, height=36, corner_radius=18, placeholder_text="Search files...", fg_color=("#FFFFFF", "#1F2937"), border_color=("#E5E7EB", "#374151"), border_width=1, text_color=("#1F2937", "#F9FAFB"), font=("Inter", 12))
        search.pack(side="right", padx=15)
        search.bind("<FocusIn>", lambda e: search.configure(border_color=("#6366F1", "#818CF8")))
        search.bind("<FocusOut>", lambda e: search.configure(border_color=("#E5E7EB", "#374151")))

        self.browse_btn = ctk.CTkButton(
            right,
            text="📁 Browse",
            width=88,
            height=34,
            corner_radius=10,
            fg_color=("#FFFFFF", "#1F2937"),
            border_color=("#6366F1", "#818CF8"),
            border_width=1,
            hover_color=("#F3F4F6", "#374151"),
            text_color=("#6366F1", "#818CF8"),
            command=self.open_folder_dialog,
            font=("Inter", 12)
        )
        self.browse_btn.pack(side="right", padx=8)

        return frame
    
    def create_preview_panel(self):
        frame_bg = ("#FFFFFF", "#1F2937")
        text_color = ("#1F2937", "#F9FAFB")

        frame = ctk.CTkFrame(self, fg_color=frame_bg, border_width=1, border_color=("#E5E7EB", "#374151"), corner_radius=12)

        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(frame, fg_color="transparent", height=40)
        header.pack(fill="x", padx=20, pady=(20, 6))

        preview_label = ctk.CTkLabel(header, text="Selection", font=("Inter", 12, "bold"), text_color=text_color)
        preview_label.pack(side="left")

        # ── Model Selector ────────────────────────────────────────────────
        model_section = ctk.CTkFrame(frame, fg_color="transparent")
        model_section.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            model_section,
            text="🤖  Model",
            font=("Inter", 10, "bold"),
            text_color=("#6B7280", "#9CA3AF"),
        ).pack(side="left", padx=(0, 6))

        self._model_var = ctk.StringVar(value=ollama_manager.get_active_model())
        self.model_selector = ctk.CTkOptionMenu(
            model_section,
            variable=self._model_var,
            values=[ollama_manager.get_active_model()],
            width=160,
            height=26,
            corner_radius=8,
            fg_color=("#F3F4F6", "#111827"),
            button_color=("#E5E7EB", "#374151"),
            button_hover_color=("#D1D5DB", "#4B5563"),
            text_color=("#1F2937", "#F9FAFB"),
            font=("Inter", 10),
            dropdown_font=("Inter", 10),
            command=self._on_model_changed,
        )
        self.model_selector.pack(side="left")

        self.refresh_model_btn = ctk.CTkButton(
            model_section,
            text="↻",
            width=26,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=("#E5E7EB", "#374151"),
            hover_color=("#E5E7EB", "#374151"),
            text_color=("#6B7280", "#9CA3AF"),
            font=("Inter", 14),
            command=self._refresh_model_list,
        )
        self.refresh_model_btn.pack(side="left", padx=(6, 0))

        # ── Ollama pull progress bar (hidden until pulling) ────────────────
        self.pull_bar = ctk.CTkProgressBar(
            frame, height=4, corner_radius=2,
            progress_color=("#F59E0B", "#D97706"),
            fg_color=("#FEF3C7", "#292524"),
        )
        self.pull_bar.set(0)
        # Not packed yet — shown only while pulling

        self.pull_label = ctk.CTkLabel(
            frame,
            text="",
            font=("Inter", 9),
            text_color=("#92400E", "#FCD34D"),
        )
        # Not packed yet

        # ── Selection box ─────────────────────────────────────────────────
        self.preview_box = ctk.CTkFrame(frame, fg_color="transparent")
        self.preview_box.pack(fill="both", expand=True, padx=12, pady=(2, 8))

        self.preview_msg = ctk.CTkLabel(
            self.preview_box, text="No file selected.",
            font=("Inter", 10), text_color=("#6B7280", "#9CA3AF"), justify="left"
        )
        self.preview_msg.pack(anchor="w", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(
            self.preview_box, width=200, height=6, corner_radius=3,
            progress_color=("#6366F1", "#818CF8")
        )
        self.progress_bar.set(0)

        controls = ctk.CTkFrame(self.preview_box, fg_color="transparent")
        controls.pack(anchor="w")

        self.type_sorter_btn = ctk.CTkButton(
            controls,
            text="Type Sorter",
            width=110,
            height=28,
            corner_radius=8,
            fg_color=("#E5E7EB", "#111827"),
            hover_color=("#F3F4F6", "#374151"),
            text_color=("#1F2937", "#F9FAFB"),
            font=("Inter", 10, "bold"),
            command=self.run_type_sorter,
            state="disabled"
        )
        self.type_sorter_btn.pack(side="left", padx=(0, 8))

        self.ai_button = ctk.CTkButton(
            controls,
            text="AI Scan",
            width=90,
            height=28,
            corner_radius=8,
            fg_color=("#6366F1", "#818CF8"),
            hover_color=("#818CF8", "#4F46E5"),
            text_color="#FFFFFF",
            font=("Inter", 10, "bold"),
            command=self.run_ai_scan,
            state="disabled"
        )
        self.ai_button.pack(side="left")

        self.undo_btn = ctk.CTkButton(
            controls,
            text="Undo Scan",
            width=80,
            height=28,
            corner_radius=8,
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            text_color="#FFFFFF",
            font=("Inter", 10, "bold"),
            command=self.run_undo_scan,
        )
        self.undo_btn.pack(side="left", padx=(8, 0))

        return frame

    # ── Model selector helpers ─────────────────────────────────────────────

    def _on_model_changed(self, model_name: str):
        """Called when user picks a different model."""
        ollama_manager.set_active_model(model_name)
        self._model_var.set(model_name)
        self.preview_msg.configure(text=f"Model set to {model_name}")

    def _refresh_model_list(self):
        """Query Ollama for locally available models and update the dropdown."""
        def _fetch():
            models = ollama_manager.get_available_models()
            self.after(0, lambda: self._apply_model_list(models))

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_model_list(self, models):
        """Update model dropdown with fresh model list (must run on main thread)."""
        if not models:
            return
        current = ollama_manager.get_active_model()
        self.model_selector.configure(values=models)
        if current in models:
            self._model_var.set(current)
        else:
            self._model_var.set(models[0])
            ollama_manager.set_active_model(models[0])

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
        self.theme_btn.configure(text=self.get_theme_icon())
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

            # ── Preview panel: progress bar + detail line
            try:
                self.pull_bar.pack(fill="x", padx=12, pady=(0, 0))
                self.pull_label.pack(anchor="w", padx=12, pady=(0, 4))

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
        if getattr(self.file_list, 'current_directory', None):
            try:
                self.type_sorter_btn.configure(state="normal")
                self.ai_button.configure(state="normal")
            except Exception:
                pass
        else:
            try:
                self.type_sorter_btn.configure(state="disabled")
                self.ai_button.configure(state="disabled")
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

        self.preview_msg.configure(text="Starting AI Scan...")
        self.ai_button.configure(state="disabled")
        
        # Show progress bar
        self.progress_bar.pack(anchor="w", pady=(0, 10))
        self.progress_bar.set(0)
        self.update()

        def update_progress(current, total, msg):
            # Must run on main thread
            self.after(0, lambda: self._update_progress_ui(current, total, msg))

        def background_task():
            # Run AI organization through the bridge
            result = self.bridge.ai_organize_folder(directory, progress_callback=update_progress)
            
            # Schedule the UI update back on the main thread
            self.after(0, lambda: self._on_ai_scan_complete(directory, result))
            
        threading.Thread(target=background_task, daemon=True).start()

    def _update_progress_ui(self, current, total, msg):
        self.preview_msg.configure(text=msg)
        if total > 0:
            self.progress_bar.set(current / total)
        else:
            self.progress_bar.set(0)

    def _on_ai_scan_complete(self, directory, result):
        self.ai_button.configure(state="normal")
        self.progress_bar.pack_forget() # hide progress bar
        if "error" in result:
            self.preview_msg.configure(text=f"AI Error: {result['error']}")
            return

        self.preview_msg.configure(text="AI Scan complete!")
        self.show_ai_scan_preview(directory, result)

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
        
        if not groups:
            ctk.CTkLabel(scroll, text="No files were organized.", font=("Inter", 12), text_color=("#111827", "#F9FAFB")).pack(pady=20)
        else:
            for group in groups:
                group_name = group.get('folder_name', 'Unknown Folder')
                files = group.get('files', [])
                
                section = ctk.CTkFrame(scroll, fg_color=("#F3F4F6", "#111827"), corner_radius=10)
                section.pack(fill="x", padx=10, pady=8)

                title = ctk.CTkLabel(section, text=f"{group_name} ({len(files)})", font=("Inter", 12, "bold"), anchor="w")
                title.pack(fill="x", padx=12, pady=(10, 4))

                body = ctk.CTkFrame(section, fg_color=("#FFFFFF", "#111827"), corner_radius=8)
                body.pack(fill="x", padx=12, pady=(0, 10))

                for item in files:
                    item_row = ctk.CTkFrame(body, fg_color=("#F9FAFB", "#1F2937"), corner_radius=6)
                    item_row.pack(fill="x", padx=6, pady=4)
                    
                    file_name = item.get('file_name', 'Unknown')
                    original = item.get('original_path', file_name)
                    
                    text_str = f"File: {original}"
                    ctk.CTkLabel(item_row, text=text_str, font=("Inter", 10), justify="left", anchor="w", wraplength=480).pack(fill="x", padx=10, pady=6)

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