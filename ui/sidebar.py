import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=170, corner_radius=0, fg_color="transparent")
        
        self.active_btn = None
        self.update_colors()

    def update_colors(self):
        """Update sidebar colors based on theme"""
        # Using tuples automatically handles Dark/Light modes!
        self.configure(fg_color="transparent", border_width=0)
        self.btn_text_color = ("#6B7280", "#9CA3AF")
        self.btn_hover_color = ("#F9FAFB", "#374151")
        
        self.create_sidebar()

    def create_sidebar(self):
        """Create sidebar content"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        title = ctk.CTkLabel(
            self,
            text="Menu",
            font=("Inter", 11, "bold"),
            text_color=("#6366F1", "#818CF8")
        )
        title.pack(pady=(25, 10), padx=25, anchor="w")

        self.buttons = []
        options = [
            ("🏠", "Home"), ("🤖", "AI Organizer"), ("🗑️", "Trash"), ("⚙️", "Settings")
        ]

        for icon, item in options:
            btn = ctk.CTkButton(
                self,
                text=f"{icon}   {item}",
                anchor="w",
                height=34,
                corner_radius=6,
                fg_color="transparent",
                text_color=self.btn_text_color,
                hover_color=self.btn_hover_color,
                font=("Inter", 12)
            )
            btn.pack(fill="x", padx=15, pady=2)
            btn.configure(command=lambda b=btn, t=item: self.set_active(b, t))
            self.buttons.append(btn)


    def set_active(self, btn, title):
        """Set active button"""
        if self.active_btn:
            self.active_btn.configure(fg_color="transparent", text_color=self.btn_text_color)

        btn.configure(fg_color=("#CCFBF1", "#005C66"), text_color=("#0D9488", "#00E5FF"))
        self.active_btn = btn