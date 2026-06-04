import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=220, corner_radius=0, fg_color="transparent")
        
        self.active_btn = None
        self.update_colors()

    def update_colors(self):
        """Update sidebar colors based on theme"""
        self.configure(
            fg_color=("#FFFFFF", "#111827"),
            border_width=1,
            border_color=("#E5E7EB", "#1F2937")
        )
        self.btn_text_color = ("#4B5563", "#9CA3AF")
        self.btn_hover_color = ("#F3F4F6", "#1F2937")
        
        self.create_sidebar()

    def create_sidebar(self):
        """Create sidebar content"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Top menu container (expand=True is removed so it packs closely at the top)
        self.top_menu = ctk.CTkFrame(self, fg_color="transparent")
        self.top_menu.pack(side="top", fill="x", expand=False)

        title = ctk.CTkLabel(
            self.top_menu,
            text="Menu",
            font=("Inter", 11, "bold"),
            text_color=("#6366F1", "#818CF8")
        )
        title.pack(pady=(20, 12), padx=20, anchor="w")

        self.buttons = []
        options = [
            ("🏠", "Home"), ("🤖", "AI Organizer"), ("🗑️", "Trash"), ("⚙️", "Settings")
        ]

        for icon, item in options:
            btn = ctk.CTkButton(
                self.top_menu,
                text=f"{icon}   {item}",
                anchor="w",
                height=40,
                corner_radius=12,
                fg_color="transparent",
                text_color=self.btn_text_color,
                hover_color=self.btn_hover_color,
                font=("Inter", 13)
            )
            btn.pack(fill="x", padx=16, pady=4)
            btn.configure(command=lambda b=btn, t=item: self.set_active(b, t))
            self.buttons.append(btn)

        # Bottom menu container for Dark Mode toggle switch
        self.bottom_menu = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_menu.pack(side="bottom", fill="x", pady=(10, 20))

        # Top separator for theme footer
        separator = ctk.CTkFrame(self.bottom_menu, height=1, fg_color=("#E5E7EB", "#1F2937"))
        separator.pack(fill="x", padx=16, pady=(0, 12))

        # Theme Section Title
        theme_label = ctk.CTkLabel(
            self.bottom_menu,
            text="Theme",
            font=("Inter", 11, "bold"),
            text_color=("#6B7280", "#9CA3AF")
        )
        theme_label.pack(padx=20, pady=(0, 6), anchor="w")

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
        self.theme_switch.pack(padx=20, pady=(0, 10), anchor="w")

    def set_active(self, btn, title):
        """Set active button with premium state styling"""
        if self.active_btn:
            self.active_btn.configure(
                fg_color="transparent", 
                text_color=self.btn_text_color,
                border_width=0
            )

        btn.configure(
            fg_color=("#EEF2FF", "#1A1D36"), 
            text_color=("#4F46E5", "#818CF8"),
            border_width=1,
            border_color=("#6366F1", "#818CF8")
        )
        self.active_btn = btn