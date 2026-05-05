import customtkinter as ctk

class FileList(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True)

        self.load_files()

    def get_colors(self):
        """Get theme-aware colors"""
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            return {
                "card_bg": "#1f2933",
                "card_hover": "#2d3748",
                "card_border": "#2d3748",
                "card_border_hover": "#3b82f6",
                "text_primary": "#e5e7eb",
                "text_secondary": "#9ca3af",
                "text_hover": "#ffffff"
            }
        else:  # Light mode
            return {
                "card_bg": "#ffffff",
                "card_hover": "#f3f4f6",
                "card_border": "#e5e7eb",
                "card_border_hover": "#3b82f6",
                "text_primary": "#1f2937",
                "text_secondary": "#6b7280",
                "text_hover": "#111827"
            }

    def load_files(self):
        files = [
            ("📄 report.pdf", "2 MB", "Today"),
            ("🖼 photo.png", "1.5 MB", "Yesterday"),
            ("🎬 video.mp4", "20 MB", "2 days ago"),
        ]

        colors = self.get_colors()

        for name, size, date in files:
            card = ctk.CTkFrame(
                self.scroll, 
                corner_radius=12, 
                height=60, 
                fg_color=colors["card_bg"],
                border_width=1,
                border_color=colors["card_border"]
            )
            card.pack(fill="x", padx=8, pady=8)

            card.grid_columnconfigure(0, weight=3)
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=1)

            name_label = ctk.CTkLabel(
                card, 
                text=name, 
                anchor="w", 
                font=("Segoe UI", 13, "bold"), 
                text_color=colors["text_primary"]
            )
            name_label.grid(row=0, column=0, padx=20, sticky="w")

            size_label = ctk.CTkLabel(
                card, 
                text=size, 
                text_color=colors["text_secondary"],
                font=("Segoe UI", 11)
            )
            size_label.grid(row=0, column=1)

            date_label = ctk.CTkLabel(
                card, 
                text=date, 
                text_color=colors["text_secondary"],
                font=("Segoe UI", 11)
            )
            date_label.grid(row=0, column=2, padx=15)

            # Direct hover effects using immediate state changes
            def on_enter(e, c=card, label=name_label, colors=colors):
                c.configure(fg_color=colors["card_hover"], border_color=colors["card_border_hover"])
                label.configure(text_color=colors["text_hover"])
            
            def on_leave(e, c=card, label=name_label, colors=colors):
                c.configure(fg_color=colors["card_bg"], border_color=colors["card_border"])
                label.configure(text_color=colors["text_primary"])

            card.bind("<Button-1>", lambda e, n=name: self.select_file(n))
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

    def select_file(self, name):
        self.master.update_preview(name)