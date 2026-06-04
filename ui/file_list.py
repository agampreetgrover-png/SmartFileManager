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
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        self.scroll.pack(fill="both", expand=True)

        self.current_directory = None
        self.show_welcome()

    def show_welcome(self):
        """Show clean modern empty welcome screen when no directory is selected"""
        colors = self.get_colors()
        self.scroll.configure(
            fg_color=colors["panel_bg"],
            border_width=1,
            border_color=colors["header_border"],
            corner_radius=12
        )

        # Clear existing widgets
        for widget in self.scroll.winfo_children():
            widget.destroy()

        # Centered container frame
        welcome_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        welcome_frame.pack(expand=True, fill="both", padx=20, pady=120)

        # Large icon
        icon_label = ctk.CTkLabel(
            welcome_frame,
            text="📁",
            font=("Inter", 64),
        )
        icon_label.pack(pady=(0, 16))

        # Title
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="No Folder Selected",
            font=("Inter", 22, "bold"),
            text_color=colors["text_primary"]
        )
        welcome_label.pack(pady=(0, 8))

        # Subtitle
        subtitle = ctk.CTkLabel(
            welcome_frame,
            text="Select a folder to begin managing files",
            font=("Inter", 13),
            text_color=colors["text_secondary"]
        )
        subtitle.pack(pady=(0, 24))

        # CTA Button
        self.cta_btn = ctk.CTkButton(
            welcome_frame,
            text="Browse Folder",
            width=160,
            height=36,
            corner_radius=8,
            fg_color=("#6366F1", "#818CF8"),
            hover_color=("#4F46E5", "#6366F1"),
            text_color="#FFFFFF",
            font=("Inter", 12, "bold"),
            command=self.master.open_folder_dialog
        )
        self.cta_btn.pack()

        # Notify parent that there is no active folder
        try:
            self.master.on_folder_changed()
        except Exception:
            pass

    def get_colors(self):
        """Get theme-aware colors"""
        return {
            "panel_bg": ("#F8FAFC", "#0F172A"),
            "header_border": ("#E2E8F0", "#1E293B"),
            "card_bg": ("#FFFFFF", "#1E293B"),
            "card_hover": ("#F9FAFB", "#334155"),
            "card_border": ("#E2E8F0", "#1E293B"),
            "card_border_hover": ("#CBD5E1", "#334155"),
            "text_primary": ("#1F2937", "#F9FAFB"),
            "text_secondary": ("#6B7280", "#9CA3AF"),
            "text_hover": ("#1F2937", "#F9FAFB")
        }

    def load_files(self, directory=None, reset_root=False):
        if directory is None:
            self.current_directory = None
            self.show_welcome()
            self.master.update_path_label(None)
            return

        if reset_root or self.current_directory is None:
            self.root_directory = directory

        self.current_directory = directory
        rel_path = os.path.relpath(directory, self.root_directory) if hasattr(self, 'root_directory') else "."
        rel_path = "." if rel_path == "." else rel_path.replace('\\', '/')
        self.master.update_path_label(rel_path)

        # Clear existing file cards
        for widget in self.scroll.winfo_children():
            widget.destroy()

        files = []
        try:
            if hasattr(self, 'root_directory') and self.current_directory != self.root_directory:
                files.append(("...", "", "", True, True))

            for f in sorted(os.listdir(directory), key=lambda x: (not os.path.isdir(os.path.join(directory, x)), x.lower())):
                path = os.path.join(directory, f)
                mod_time = os.path.getmtime(path)
                date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
                if os.path.isdir(path):
                    size = "—"
                    files.append((f, size, date_str, True, False))
                else:
                    size = format_size(os.path.getsize(path))
                    files.append((f, size, date_str, False, False))
        except Exception as e:
            files.append((f"Error reading directory: {e}", "", "", False, False))

        colors = self.get_colors()
        self.scroll.configure(fg_color=colors["card_bg"])

        # Add headers wrapper
        header_wrapper = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header_wrapper.pack(fill="x", padx=6, pady=(10, 10))

        header_frame = ctk.CTkFrame(header_wrapper, fg_color="transparent", height=20)
        header_frame.pack(fill="x")
        header_frame.grid_columnconfigure(0, weight=3, uniform="col")
        header_frame.grid_columnconfigure(1, weight=1, uniform="col")
        header_frame.grid_columnconfigure(2, weight=1, uniform="col")
        header_frame.grid_columnconfigure(3, weight=1, uniform="col")

        ctk.CTkLabel(header_frame, text="Name", font=("Inter", 11, "bold"), text_color=("#6366F1", "#818CF8")).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(header_frame, text="Size", font=("Inter", 11, "bold"), text_color=("#6366F1", "#818CF8")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(header_frame, text="Date Modified", font=("Inter", 11, "bold"), text_color=("#6366F1", "#818CF8")).grid(row=0, column=2, sticky="w", padx=15)
        ctk.CTkLabel(header_frame, text="Type", font=("Inter", 11, "bold"), text_color=("#6366F1", "#818CF8")).grid(row=0, column=3, sticky="w", padx=10)

        # Subtle separator line below headers
        separator = ctk.CTkFrame(header_wrapper, height=1, fg_color=colors["header_border"])
        separator.pack(fill="x", pady=(8, 0))

        for name, size, date, is_dir, is_special in files:
            if is_special:
                icon = "↩"
                display_name = "..."
                ext_label = "UP"
            elif is_dir:
                icon = "📁"
                ext_label = "DIR"
                display_name = f"{icon}  {name}"
            else:
                ext = name.split(".")[-1].lower() if "." in name else ""
                icon = "📄"
                if ext in ["jpg", "png", "jpeg", "gif", "webp"]:
                    icon = "🖼️"
                elif ext in ["mp4", "mkv", "avi", "mov"]:
                    icon = "🎬"
                elif ext in ["mp3", "wav", "flac"]:
                    icon = "🎵"
                elif ext in ["zip", "rar", "tar", "gz"]:
                    icon = "📦"
                elif ext in ["pdf"]:
                    icon = "📕"
                elif ext in ["doc", "docx", "txt"]:
                    icon = "📝"
                elif ext in ["py", "js", "html", "css", "json", "md"]:
                    icon = "💻"
                ext_label = ext.upper() if ext else "FILE"
                display_name = f"{icon}  {name}"

            card = ctk.CTkFrame(
                self.scroll, 
                corner_radius=12, 
                height=38, 
                fg_color=colors["card_bg"],
                border_width=1,
                border_color=colors["card_border"]
            )
            card.pack(fill="x", padx=6, pady=2)

            card.grid_columnconfigure(0, weight=3, uniform="col")
            card.grid_columnconfigure(1, weight=1, uniform="col")
            card.grid_columnconfigure(2, weight=1, uniform="col")
            card.grid_columnconfigure(3, weight=1, uniform="col")

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

            type_label = ctk.CTkLabel(
                card,
                text=ext_label,
                font=("Inter", 10, "bold"),
                text_color=colors["text_secondary"],
                fg_color="transparent"
            )
            type_label.grid(row=0, column=3, sticky="w", padx=10)

            if not is_special:
                dots_label = ctk.CTkLabel(card, text="⋮", font=("Inter", 16, "bold"), text_color=colors["text_secondary"])
                dots_label.grid(row=0, column=4, padx=15)

            # Direct hover effects using immediate state changes
            def on_enter(e, c=card, label=name_label, colors=colors):
                c.configure(fg_color=colors["card_hover"], border_color=colors["card_border_hover"])
                label.configure(text_color=colors["text_hover"])
            
            def on_leave(e, c=card, label=name_label, colors=colors):
                c.configure(fg_color=colors["card_bg"], border_color=colors["card_border"])
                label.configure(text_color=colors["text_primary"])

            card.bind("<Button-1>", lambda e, n=name, d=is_dir, s=is_special: self.open_item(n, d, s))
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

        # Footer items count
        footer = ctk.CTkLabel(self.scroll, text=f"{len(files)} items", font=("Inter", 11), text_color=("#6B7280", "#809A9E"))
        footer.pack(pady=20)
        # Notify parent that folder changed (enable/disable controls)
        try:
            self.master.on_folder_changed()
        except Exception:
            pass

    def open_item(self, name, is_dir, is_special=False):
        if is_special:
            parent = os.path.dirname(self.current_directory)
            root = getattr(self, 'root_directory', None)
            if root and os.path.abspath(parent).startswith(os.path.abspath(root)):
                self.load_files(parent)
            else:
                self.load_files(root)
            return

        full_path = os.path.join(getattr(self, 'current_directory', '.'), name)
        if is_dir:
            self.load_files(full_path)
        else:
            self.master.update_preview(name, full_path)