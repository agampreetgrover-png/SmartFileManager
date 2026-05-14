import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.file_list import FileList
import threading
import time
import os

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

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="ns", pady=0)
        
        self.topbar = self.create_topbar()
        self.topbar.grid(row=0, column=1, columnspan=2, sticky="ew")

        self.file_list = FileList(self)
        self.file_list.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))

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
        indicator_color = ("#6366F1", "#818CF8")
        
        frame = ctk.CTkFrame(self, fg_color=frame_bg, border_width=1, border_color=("#E5E7EB", "#374151"), corner_radius=12)

        header = ctk.CTkFrame(frame, fg_color="transparent", height=40)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        preview_label = ctk.CTkLabel(header, text="Selection", font=("Inter", 14, "bold"), text_color=text_color)
        preview_label.pack(side="left")

        # Details Content Frame
        self.preview_box = ctk.CTkFrame(frame, fg_color="transparent")
        self.preview_box.pack(fill="both", expand=True, padx=20, pady=0)

        self.preview_msg = ctk.CTkLabel(self.preview_box, text="No file selected.", font=("Inter", 12), text_color=("#6B7280", "#9CA3AF"), justify="left")
        self.preview_msg.pack(anchor="w", pady=(0, 12))

        ai_header = ctk.CTkLabel(self.preview_box, text="AI Insights", font=("Inter", 12, "bold"), text_color=("#6B7280", "#9CA3AF"))
        ai_header.pack(anchor="w", pady=(0, 8))

        self.lbl_ai_val = ctk.CTkLabel(self.preview_box, text="Select a file to enable AI insights.", font=("Inter", 12), text_color=("#111827", "#E0E0E0"), justify="left")
        self.lbl_ai_val.pack(anchor="w", pady=(0, 10))

        self.ai_button = ctk.CTkButton(
            self.preview_box,
            text="Run AI Scan",
            width=120,
            height=34,
            corner_radius=8,
            fg_color=("#6366F1", "#818CF8"),
            hover_color=("#818CF8", "#4F46E5"),
            text_color="#FFFFFF",
            font=("Inter", 11, "bold"),
            command=self.show_ai_popup,
            state="disabled"
        )
        self.ai_button.pack(anchor="w", pady=(10, 0))

        return frame

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
        self.lbl_ai_val.configure(text="Ready to run AI scan.")
        self.ai_button.configure(state="normal")

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

    def show_ai_popup(self):
        if not hasattr(self, 'selected_file') or not self.selected_file:
            # Show error in preview panel dynamically
            self.lbl_ai_val.configure(text="[!] Please select a file first.")
            return

        win_bg = ("#F3F4F6", "#050C0F")
        card_bg = ("#FFFFFF", "#061519")
        card_border = ("#0D9488", "#00E5FF")
        progress_bg = ("#F9FAFB", "#071E22")
        progress_fill = ("#0D9488", "#00E5FF")
        text_main = ("#111827", "#FFFFFF")
        text_secondary = ("#6B7280", "#809A9E")
        text_tertiary = ("#6B7280", "#809A9E")
        btn_text = "#FFFFFF"
        
        win = ctk.CTkToplevel(self)
        win.geometry("380x420")
        win.title("AI Analysis")
        win.configure(fg_color=win_bg)
        win.attributes('-alpha', 0.98)

        card = ctk.CTkFrame(win, corner_radius=12, fg_color=card_bg, border_width=1, border_color=card_border)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(card, text="AI Classification", font=("Inter", 18, "bold"), text_color=text_main)
        header.pack(pady=(15, 10))
        
        # Analyze the file using the bridge
        file_path = self.selected_file
        
        # For testing purposes: Create dummy file if it doesn't exist so Ollama can read it
        import os
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(f"This is a dummy content for {file_path}")

        # Call the backend
        win.update() # Force UI update before blocking call
        result = self.bridge.analyze_file(file_path)
        
        category = result.get("category", "Unknown")
        confidence = result.get("confidence", 0.0)
        source = result.get("source", "Unknown")
        
        progress_frame = ctk.CTkFrame(card, fg_color=progress_bg, corner_radius=8)
        progress_frame.pack(pady=10, padx=15, fill="x")
        
        progress_bar = ctk.CTkProgressBar(progress_frame, fg_color=progress_fill, progress_color="#3b82f6")
        progress_bar.pack(fill="x", padx=8, pady=8)
        progress_bar.set(confidence)
        
        ctk.CTkLabel(card, text=f"Category: {category}", text_color=text_secondary, font=("Inter", 12)).pack()
        ctk.CTkLabel(card, text=f"Source: {source}", text_color=text_tertiary, font=("Inter", 11)).pack()
        conf_pct = int(confidence * 100)
        ctk.CTkLabel(card, text=f"Confidence: {conf_pct}%", text_color=("#0D9488", "#00E5FF"), font=("Inter", 12, "bold")).pack(pady=(5, 15))

        move_btn = ctk.CTkButton(card, text="Move to Suggested Folder", fg_color=("#0D9488", "#005C66"), hover_color=("#0F766E", "#008080"), text_color=btn_text, font=("Inter", 12, "bold"))
        move_btn.pack(pady=10)
        
        def button_press():
            move_btn.configure(text="✓ Moving...")
            self.after(800, lambda: win.destroy())
        
        move_btn.configure(command=button_press)

        # Level 3 Feedback System UI
        ctk.CTkLabel(card, text="Incorrect? Teach the AI:", text_color=text_secondary, font=("Segoe UI", 10)).pack(pady=(10, 0))
        
        correction_frame = ctk.CTkFrame(card, fg_color="transparent")
        correction_frame.pack(pady=5)
        
        correct_entry = ctk.CTkEntry(correction_frame, placeholder_text="Correct Category", width=120, height=28)
        correct_entry.pack(side="left", padx=5)
        
        def submit_correction():
            new_cat = correct_entry.get().strip()
            if new_cat:
                self.bridge.user_correction(file_path, new_cat)
                win.destroy()
                self.lbl_ai_val.configure(text=f"[Feedback Saved]\nLearned: {new_cat}")

        correct_btn = ctk.CTkButton(correction_frame, text="Correct", width=60, height=28, fg_color="#6b7280", hover_color="#4b5563", command=submit_correction)
        correct_btn.pack(side="left")