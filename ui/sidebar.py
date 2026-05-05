import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=220, corner_radius=0)
        
        self.active_btn = None
        self.update_colors()

    def update_colors(self):
        """Update sidebar colors based on theme"""
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            self.configure(fg_color="#111827", border_width=1, border_color="#2d3748")
            self.title_color = "#e5e7eb"
            self.btn_text_color = "#d1d5db"
            self.btn_hover_color = "#1f2933"
        else:  # Light mode
            self.configure(fg_color="#f9fafb", border_width=1, border_color="#e5e7eb")
            self.title_color = "#1f2937"
            self.btn_text_color = "#4b5563"
            self.btn_hover_color = "#e8e0f8"
        
        self.create_sidebar()

    def create_sidebar(self):
        """Create sidebar content"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        title = ctk.CTkLabel(
            self,
            text="Smart Manager",
            font=("Segoe UI", 20, "bold"),
            text_color=self.title_color
        )
        title.pack(pady=(20, 30))

        self.buttons = []
        options = [
            "Home", "Downloads", "Documents",
            "Desktop", "Favorites", "AI Organizer", "Settings"
        ]

        for item in options:
            btn = ctk.CTkButton(
                self,
                text=item,
                anchor="w",
                height=40,
                corner_radius=10,
                fg_color="transparent",
                text_color=self.btn_text_color,
                hover_color=self.btn_hover_color,
                font=("Segoe UI", 12)
            )
            btn.pack(fill="x", padx=10, pady=6)
            btn.configure(command=lambda b=btn, t=item: self.set_active(b, t))
            self.buttons.append(btn)

    def set_active(self, btn, title):
        """Set active button"""
        if self.active_btn:
            self.active_btn.configure(fg_color="transparent", text_color=self.btn_text_color)

        btn.configure(fg_color="#3b82f6", text_color="#ffffff")
        self.active_btn = btn