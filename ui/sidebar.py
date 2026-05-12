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
        self.btn_text_color = ("#6B7280", "#809A9E")
        self.btn_hover_color = ("#F3F4F6", "#071E22")
        
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
            text_color=("#0D9488", "#00E5FF")
        )
        title.pack(pady=(25, 10), padx=25, anchor="w")

        self.buttons = []
        options = [
            ("🏠", "Home"), ("📥", "Downloads"), ("📄", "Documents"),
            ("💻", "Desktop"), ("⭐", "Favorites"), ("🤖", "AI Organizer"), ("🗑️", "Trash"), ("⚙️", "Settings")
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

        # Storage widget at the bottom
        storage_frame = ctk.CTkFrame(self, fg_color=("#F3F4F6", "#050C0F"), border_width=1, border_color=("#E5E7EB", "#10353A"), corner_radius=12)
        storage_frame.pack(side="bottom", fill="x", padx=15, pady=25)

        s_title = ctk.CTkLabel(storage_frame, text="Storage", font=("Inter", 10, "bold"), text_color=("#0D9488", "#00E5FF"))
        s_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Fake Circular Progress using labels and shapes
        circle_frame = ctk.CTkFrame(storage_frame, width=60, height=60, corner_radius=30, fg_color="transparent", border_width=4, border_color=("#0D9488", "#00E5FF"))
        circle_frame.pack(pady=5)
        circle_frame.pack_propagate(False)

        pct_label = ctk.CTkLabel(circle_frame, text="68%", font=("Inter", 12, "bold"), text_color=("#111827", "#FFFFFF"))
        pct_label.pack(expand=True)

        info_label = ctk.CTkLabel(storage_frame, text="34.2 GB / 50 GB", font=("Inter", 10), text_color=("#6B7280", "#809A9E"))
        info_label.pack(pady=(10, 5))

        line = ctk.CTkFrame(storage_frame, height=4, corner_radius=2, fg_color=("#0D9488", "#00E5FF"), width=50)
        line.pack(pady=(0, 15))

    def set_active(self, btn, title):
        """Set active button"""
        if self.active_btn:
            self.active_btn.configure(fg_color="transparent", text_color=self.btn_text_color)

        btn.configure(fg_color=("#CCFBF1", "#005C66"), text_color=("#0D9488", "#00E5FF"))
        self.active_btn = btn