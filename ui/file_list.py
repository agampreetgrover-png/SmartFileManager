import os
import math
from datetime import datetime
import customtkinter as ctk

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"
class FileList(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.master = master
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=12, border_width=1, border_color="#10353A")
        self.scroll.pack(fill="both", expand=True)

        self.load_files()

    def get_colors(self):
        """Get theme-aware colors"""
        return {
            "panel_bg": ("#FFFFFF", "#061519"),
            "header_border": ("#E5E7EB", "#10353A"),
            "card_bg": ("#FFFFFF", "#071E22"),
            "card_hover": ("#F9FAFB", "#0A262A"),
            "card_border": ("#FFFFFF", "#071E22"),
            "card_border_hover": ("#E5E7EB", "#10353A"),
            "text_primary": ("#111827", "#E0E0E0"),
            "text_secondary": ("#6B7280", "#809A9E"),
            "text_hover": ("#111827", "#FFFFFF")
        }

    def load_files(self, directory="."):
        self.current_directory = directory
        # Clear existing file cards
        for widget in self.scroll.winfo_children():
            widget.destroy()

        files = []
        try:
            for f in os.listdir(directory):
                path = os.path.join(directory, f)
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    mod_time = os.path.getmtime(path)
                    date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
                    files.append((f, format_size(size), date_str))
        except Exception as e:
            files.append((f"Error reading directory: {e}", "", ""))

        colors = self.get_colors()
        self.scroll.configure(fg_color=colors["panel_bg"])

        # Add headers wrapper
        header_wrapper = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header_wrapper.pack(fill="x", padx=6, pady=(10, 10))

        header_frame = ctk.CTkFrame(header_wrapper, fg_color="transparent", height=20)
        header_frame.pack(fill="x")
        header_frame.grid_columnconfigure(0, weight=3)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=1)
        header_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(header_frame, text="Name", font=("Inter", 11, "bold"), text_color=("#0D9488", "#00E5FF")).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(header_frame, text="Size", font=("Inter", 11, "bold"), text_color=("#0D9488", "#00E5FF")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(header_frame, text="Date Modified", font=("Inter", 11, "bold"), text_color=("#0D9488", "#00E5FF")).grid(row=0, column=2, sticky="w", padx=15)
        ctk.CTkLabel(header_frame, text="Type", font=("Inter", 11, "bold"), text_color=("#0D9488", "#00E5FF")).grid(row=0, column=3, sticky="w", padx=10)

        # Subtle separator line below headers
        separator = ctk.CTkFrame(header_wrapper, height=1, fg_color=colors["header_border"])
        separator.pack(fill="x", pady=(8, 0))

        for name, size, date in files:
            ext = name.split(".")[-1].lower() if "." in name else ""
            icon = "📄"
            if ext in ["jpg", "png", "jpeg", "gif", "webp"]: icon = "🖼️"
            elif ext in ["mp4", "mkv", "avi", "mov"]: icon = "🎬"
            elif ext in ["mp3", "wav", "flac"]: icon = "🎵"
            elif ext in ["zip", "rar", "tar", "gz"]: icon = "📦"
            elif ext in ["pdf"]: icon = "📕"
            elif ext in ["doc", "docx", "txt"]: icon = "📝"
            elif ext in ["py", "js", "html", "css", "json", "md"]: icon = "💻"
            elif os.path.isdir(os.path.join(self.current_directory, name)): icon = "📁"
            
            display_name = f"{icon}  {name}"

            card = ctk.CTkFrame(
                self.scroll, 
                corner_radius=6, 
                height=38, 
                fg_color=colors["card_bg"],
                border_width=1,
                border_color=colors["card_border"]
            )
            card.pack(fill="x", padx=6, pady=2)

            card.grid_columnconfigure(0, weight=3)
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=1)
            card.grid_columnconfigure(3, weight=1)

            name_label = ctk.CTkLabel(
                card, 
                text=display_name, 
                anchor="w", 
                font=("Inter", 12), 
                text_color=colors["text_primary"]
            )
            name_label.grid(row=0, column=0, padx=10, sticky="w")

            size_label = ctk.CTkLabel(
                card, 
                text=size, 
                anchor="w",
                text_color=colors["text_secondary"],
                font=("Inter", 12)
            )
            size_label.grid(row=0, column=1, sticky="w")

            date_label = ctk.CTkLabel(
                card, 
                text=date, 
                anchor="w",
                text_color=colors["text_secondary"],
                font=("Inter", 12)
            )
            date_label.grid(row=0, column=2, padx=15, sticky="w")

            type_frame = ctk.CTkFrame(card, fg_color=("#CCFBF1", "#052E33"), corner_radius=10, height=20)
            type_frame.grid(row=0, column=3, sticky="w", padx=10)
            type_label = ctk.CTkLabel(type_frame, text=ext.upper() if ext else "FILE", font=("Inter", 9, "bold"), text_color=("#0D9488", "#00E5FF"))
            type_label.pack(padx=8, pady=2)

            dots_label = ctk.CTkLabel(card, text="⋮", font=("Inter", 16, "bold"), text_color=colors["text_secondary"])
            dots_label.grid(row=0, column=4, padx=15)

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

        # Footer items count
        footer = ctk.CTkLabel(self.scroll, text=f"{len(files)} items", font=("Inter", 11), text_color=("#6B7280", "#809A9E"))
        footer.pack(pady=20)

    def select_file(self, name):
        full_path = os.path.join(getattr(self, 'current_directory', '.'), name)
        self.master.update_preview(name, full_path)