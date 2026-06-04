import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=200, corner_radius=0, fg_color="transparent")
        
        self.active_btn = None
        self.update_colors()

    def update_colors(self):
        """Update sidebar colors based on theme"""
        # Using a distinct card background and right border for visual division
        self.configure(
            fg_color=("#FFFFFF", "#1F2937"),
            border_width=1,
            border_color=("#E5E7EB", "#374151")
        )
        self.btn_text_color = ("#6B7280", "#9CA3AF")
        self.btn_hover_color = ("#F9FAFB", "#374151")
        
        self.create_sidebar()

    def create_sidebar(self):
        """Create sidebar content"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Top menu container for title and buttons
        self.top_menu = ctk.CTkFrame(self, fg_color="transparent")
        self.top_menu.pack(side="top", fill="both", expand=True)

        title = ctk.CTkLabel(
            self.top_menu,
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
                self.top_menu,
                text=f"{icon}   {item}",
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                text_color=self.btn_text_color,
                hover_color=self.btn_hover_color,
                font=("Inter", 13)
            )
            btn.pack(fill="x", padx=15, pady=10, expand=True)
            btn.configure(command=lambda b=btn, t=item: self.set_active(b, t))
            self.buttons.append(btn)

        # Bottom menu container for Dark Mode toggle switch
        self.bottom_menu = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_menu.pack(side="bottom", fill="x", pady=20)

        # Dark Mode Switch
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.switch_var = ctk.StringVar(value="on" if is_dark else "off")
        
        self.theme_switch = ctk.CTkSwitch(
            self.bottom_menu,
            text="Dark Mode",
            variable=self.switch_var,
            onvalue="on",
            offvalue="off",
            command=self.master.toggle_theme,
            font=("Inter", 12),
            text_color=self.btn_text_color,
            progress_color=("#6366F1", "#818CF8")
        )
        self.theme_switch.pack(padx=20, pady=10, anchor="w")

    def set_active(self, btn, title):
        """Set active button"""
        if self.active_btn:
            self.active_btn.configure(fg_color="transparent", text_color=self.btn_text_color)

        btn.configure(fg_color=("#CCFBF1", "#005C66"), text_color=("#0D9488", "#00E5FF"))
        self.active_btn = btn