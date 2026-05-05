import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.file_list import FileList
import threading
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart File Manager")
        self.geometry("1350x780")
        # Modern professional background
        self.configure(fg_color="#0f172a")
        
        # Animation states
        self.ai_pulse_state = False

        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")

        self.topbar = self.create_topbar()
        self.topbar.grid(row=0, column=1, columnspan=2, sticky="ew")

        self.file_list = FileList(self)
        self.file_list.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.preview = self.create_preview_panel()
        self.preview.grid(row=1, column=2, sticky="nsew", padx=(0,10), pady=10)

    def create_topbar(self):
        mode = ctk.get_appearance_mode()
        topbar_color = "#111827" if mode == "Dark" else "#ffffff"
        border_color = "#2d3748" if mode == "Dark" else "#e5e7eb"
        
        frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=topbar_color, border_width=1, border_color=border_color)

        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15)

        mode = ctk.get_appearance_mode()
        title_color = "#e5e7eb" if mode == "Dark" else "#1f2937"
        title_hover_color = "#3b82f6" if mode == "Dark" else "#2563eb"
        
        title_label = ctk.CTkLabel(left, text="📁 Smart File Manager", font=("Segoe UI", 16, "bold"), text_color=title_color)
        title_label.pack()
        title_label.bind("<Enter>", lambda e: title_label.configure(text_color=title_hover_color))
        title_label.bind("<Leave>", lambda e: title_label.configure(text_color=title_color))

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="right", padx=10, pady=10)

        self.theme_switch = ctk.CTkSwitch(
            right,
            text="Light",
            command=self.toggle_theme,
            progress_color="#3b82f6"
        )
        self.theme_switch.pack(side="right", padx=10)

        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            search_bg = "#1f2933"
            search_border = "#2d3748"
            search_text = "#e5e7eb"
        else:
            search_bg = "#f3f4f6"
            search_border = "#d1d5db"
            search_text = "#1f2937"
        
        search = ctk.CTkEntry(right, width=220, placeholder_text="Search files...", fg_color=search_bg, border_color=search_border, text_color=search_text)
        search.pack(side="right", padx=10)
        search.bind("<FocusIn>", lambda e: search.configure(border_color="#3b82f6"))
        search.bind("<FocusOut>", lambda e: search.configure(border_color=search_border))

        self.ai_button = ctk.CTkButton(right, text="🤖 AI", width=60, command=self.show_ai_popup, fg_color="#3b82f6", hover_color="#2563eb")
        self.ai_button.pack(side="right", padx=5)
        self.animate_ai_pulse()

        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            btn_bg = "#1f2933"
            btn_hover = "#2d3748"
        else:
            btn_bg = "#f0f4f8"
            btn_hover = "#e5e7eb"
        
        ctk.CTkButton(right, text="+", width=40, fg_color=btn_bg, hover_color=btn_hover, text_color="#3b82f6").pack(side="right", padx=5)

        return frame
    
    def animate_ai_pulse(self):
        """Pulse animation for AI button"""
        def pulse():
            while True:
                try:
                    current_color = self.ai_button.cget("fg_color")
                    next_color = "#6d28d9" if current_color == "#7c3aed" else "#7c3aed"
                    self.ai_button.configure(fg_color=next_color)
                    time.sleep(0.8)
                except:
                    break
        
        threading.Thread(target=pulse, daemon=True).start()

    def create_preview_panel(self):
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            frame_bg = "#1f2933"
            frame_border = "#2d3748"
            text_color = "#e5e7eb"
            box_bg = "#0f172a"
            indicator_color = "#3b82f6"
            secondary_text = "#d1d5db"
        else:
            frame_bg = "#ffffff"
            frame_border = "#e5e7eb"
            text_color = "#1f2937"
            box_bg = "#f9fafb"
            indicator_color = "#3b82f6"
            secondary_text = "#4b5563"
        
        frame = ctk.CTkFrame(self, corner_radius=12, fg_color=frame_bg, border_width=1, border_color=frame_border)

        header = ctk.CTkFrame(frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        preview_label = ctk.CTkLabel(header, text="Preview", font=("Segoe UI", 16, "bold"), text_color=text_color)
        preview_label.pack(side="left")
        
        indicator = ctk.CTkLabel(header, text="●", text_color=indicator_color, font=("Segoe UI", 10))
        indicator.pack(side="right")

        self.preview_box = ctk.CTkTextbox(frame, height=300, fg_color=box_bg, text_color=secondary_text, border_color=frame_border, border_width=0)
        self.preview_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        return frame

    def update_preview(self, name):
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", f"Selected File:\n\n{name}\n\nDetails:\n- Size: Sample\n- Type: File\n- AI Tag: Demo")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        
        # Update all UI components with new colors
        self.after(100, self.refresh_ui_colors)
    
    def refresh_ui_colors(self):
        """Refresh all UI colors for theme change"""
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            self.configure(fg_color="#0f172a")
            self.topbar.configure(fg_color="#111827", border_color="#2d3748")
            self.preview.configure(fg_color="#1f2933", border_color="#2d3748")
        else:  # Light
            self.configure(fg_color="#f9fafb")
            self.topbar.configure(fg_color="#ffffff", border_color="#e5e7eb")
            self.preview.configure(fg_color="#ffffff", border_color="#e5e7eb")
        
        # Reload file list with new colors
        self.file_list.load_files()
        # Update sidebar colors
        self.sidebar.update_colors()

    def show_ai_popup(self):
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            win_bg = "#0f172a"
            card_bg = "#1f2933"
            card_border = "#3b82f6"
            progress_bg = "#111827"
            progress_fill = "#2d3748"
            text_main = "#e5e7eb"
            text_secondary = "#d1d5db"
            text_tertiary = "#9ca3af"
            btn_text = "#ffffff"
        else:
            win_bg = "#f9fafb"
            card_bg = "#ffffff"
            card_border = "#3b82f6"
            progress_bg = "#f0f4f8"
            progress_fill = "#e0e7ff"
            text_main = "#1f2937"
            text_secondary = "#4b5563"
            text_tertiary = "#6b7280"
            btn_text = "#ffffff"
        
        win = ctk.CTkToplevel(self)
        win.geometry("360x320")
        win.title("AI Analysis")
        win.configure(fg_color=win_bg)
        win.attributes('-alpha', 0.95)

        card = ctk.CTkFrame(win, corner_radius=15, fg_color=card_bg, border_width=1, border_color=card_border)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        header = ctk.CTkLabel(card, text="AI Classification", font=("Segoe UI", 16, "bold"), text_color=text_main)
        header.pack(pady=(15, 10))
        
        progress_frame = ctk.CTkFrame(card, fg_color=progress_bg, corner_radius=8)
        progress_frame.pack(pady=10, padx=15, fill="x")
        
        progress_bar = ctk.CTkProgressBar(progress_frame, fg_color=progress_fill, progress_color="#3b82f6")
        progress_bar.pack(fill="x", padx=8, pady=8)
        progress_bar.set(0.94)
        
        ctk.CTkLabel(card, text="Category: Images", text_color=text_secondary, font=("Segoe UI", 12)).pack()
        ctk.CTkLabel(card, text="Tags: Nature, HD", text_color=text_tertiary, font=("Segoe UI", 11)).pack()
        ctk.CTkLabel(card, text="Confidence: 94%", text_color="#3b82f6", font=("Segoe UI", 12, "bold")).pack(pady=(5, 15))

        move_btn = ctk.CTkButton(card, text="Move to Suggested Folder", fg_color="#3b82f6", hover_color="#2563eb", text_color=btn_text, font=("Segoe UI", 12, "bold"))
        move_btn.pack(pady=15)
        
        def button_press():
            move_btn.configure(text="✓ Moving...")
            self.after(800, lambda: move_btn.configure(text="Move to Suggested Folder"))
        
        move_btn.configure(command=button_press)