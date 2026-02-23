import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json
import os
import yt_dlp

# ─── Config persistence ───────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"download_path": os.path.join(os.path.expanduser("~"), "Downloads")}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── App ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

config = load_config()

class PawLoaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PawLoader 🐾")
        self.geometry("680x800")  # fixed size, not fullscreen
        self.resizable(True, True)
        self.configure(fg_color="#FFF5F7")

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.download_path = config.get("download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
        self.queue = []           # list of URLs waiting to download
        self.is_downloading = False
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header (full width)
        header = ctk.CTkFrame(self, fg_color="#FF8FAB", corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🐾  PawLoader",
            font=ctk.CTkFont(family="Georgia", size=36, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=40, pady=16)

        ctk.CTkLabel(
            header,
            text="TikTok · Instagram · YouTube & more",
            font=ctk.CTkFont(family="Georgia", size=14),
            text_color="#FFD6E0"
        ).pack(side="left", pady=28)

        # ── Cat strip
        ctk.CTkLabel(self, text="≽^•⩊•^≼  ≽^•⩊•^≼  ≽^•⩊•^≼  ≽^•⩊•^≼  ≽^•⩊•^≼",
            font=ctk.CTkFont(size=18), text_color="#FFB3C6", fg_color="#FFF5F7").pack(pady=(16, 0))

        # ── Scrollable center content (max width 820px, centered)
        outer = ctk.CTkFrame(self, fg_color="#FFF5F7")
        outer.pack(fill="both", expand=True)

        # Scrollable frame
        self.scroll = ctk.CTkScrollableFrame(outer, fg_color="#FFF5F7", scrollbar_button_color="#FFB3C6", scrollbar_button_hover_color="#FF8FAB")
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Inner centered container
        inner = ctk.CTkFrame(self.scroll, fg_color="#FFF5F7")
        inner.pack(anchor="center", pady=10)
        inner.configure(width=820)

        PAD = dict(padx=0, pady=(10, 0), fill="x")

        # ── URL Card
        url_card = ctk.CTkFrame(inner, fg_color="white", corner_radius=18, border_width=2, border_color="#FFB3C6", width=820)
        url_card.pack(**PAD)
        url_card.pack_propagate(False)

        ctk.CTkLabel(url_card, text="ENTER URL  ( single video · playlist · multiple URLs )",
            font=ctk.CTkFont(family="Georgia", size=12, weight="bold"), text_color="#FF8FAB").pack(anchor="w", padx=18, pady=(14, 2))

        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkLabel(url_row, text="🔍", font=ctk.CTkFont(size=20), fg_color="transparent").pack(side="left", padx=(0, 6))

        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="Paste URL here (video or playlist)...",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color="#FFF0F4", border_color="#FFB3C6", border_width=2,
            corner_radius=30, height=44, text_color="#333"
        )
        self.url_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(url_row, text="Paste", width=70, height=44,
            fg_color="#FFB3C6", hover_color="#FF8FAB", text_color="white",
            font=ctk.CTkFont(family="Georgia", size=12), corner_radius=30,
            command=self._paste_url).pack(side="left", padx=(8, 0))

        ctk.CTkButton(url_row, text="+ Add", width=70, height=44,
            fg_color="#FF8FAB", hover_color="#FF6B8A", text_color="white",
            font=ctk.CTkFont(family="Georgia", size=12, weight="bold"), corner_radius=30,
            command=self._add_to_queue).pack(side="left", padx=(8, 0))

        # Playlist toggle
        playlist_row = ctk.CTkFrame(url_card, fg_color="transparent")
        playlist_row.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(playlist_row, text="Playlist mode:",
            font=ctk.CTkFont(family="Georgia", size=12), text_color="#888").pack(side="left")

        self.playlist_var = ctk.StringVar(value="full")
        ctk.CTkRadioButton(playlist_row, text="Full playlist", variable=self.playlist_var, value="full",
            font=ctk.CTkFont(family="Georgia", size=12), text_color="#555",
            fg_color="#FF8FAB", hover_color="#FFB3C6").pack(side="left", padx=(12, 0))
        ctk.CTkRadioButton(playlist_row, text="Single video only", variable=self.playlist_var, value="single",
            font=ctk.CTkFont(family="Georgia", size=12), text_color="#555",
            fg_color="#FF8FAB", hover_color="#FFB3C6").pack(side="left", padx=(12, 0))

        # ── Queue Card
        queue_card = ctk.CTkFrame(inner, fg_color="white", corner_radius=18, border_width=2, border_color="#FFB3C6", width=820)
        queue_card.pack(**PAD)
        queue_card.pack_propagate(False)

        queue_header = ctk.CTkFrame(queue_card, fg_color="transparent")
        queue_header.pack(fill="x", padx=18, pady=(12, 4))

        ctk.CTkLabel(queue_header, text="📋  DOWNLOAD QUEUE",
            font=ctk.CTkFont(family="Georgia", size=12, weight="bold"), text_color="#FF8FAB").pack(side="left")

        ctk.CTkButton(queue_header, text="🗑 Clear", width=70, height=28,
            fg_color="#FFE0E8", hover_color="#FFB3C6", text_color="#FF8FAB",
            font=ctk.CTkFont(family="Georgia", size=11), corner_radius=20,
            command=self._clear_queue).pack(side="right")

        self.queue_box = ctk.CTkTextbox(
            queue_card, height=120,
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color="#FFF8FA", border_width=0, corner_radius=8,
            text_color="#888", wrap="word"
        )
        self.queue_box.pack(padx=14, pady=(0, 14), fill="x")
        self.queue_box.insert("end", "Queue is empty — add URLs above! 🐾\n")
        self.queue_box.configure(state="disabled")

        # ── Directory Card
        dir_card = ctk.CTkFrame(inner, fg_color="white", corner_radius=18, border_width=2, border_color="#FFB3C6", width=820)
        dir_card.pack(**PAD)
        dir_card.pack_propagate(False)

        ctk.CTkLabel(dir_card, text="SAVE LOCATION",
            font=ctk.CTkFont(family="Georgia", size=12, weight="bold"), text_color="#FF8FAB").pack(anchor="w", padx=18, pady=(14, 2))

        dir_row = ctk.CTkFrame(dir_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkLabel(dir_row, text="📂", font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 6))

        self.path_label = ctk.CTkLabel(dir_row, text=self.download_path,
            font=ctk.CTkFont(family="Georgia", size=12), text_color="#888", anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(dir_row, text="⬥ ⬥ ⬥  Change", height=38,
            fg_color="#FF8FAB", hover_color="#FF6B8A", text_color="white",
            font=ctk.CTkFont(family="Georgia", size=12, weight="bold"), corner_radius=30,
            command=self._pick_directory).pack(side="right")

        # ── Download Button
        self.dl_btn = ctk.CTkButton(
            inner, text="⬇   Download All", height=56,
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            fg_color="#FF8FAB", hover_color="#FF6B8A", text_color="white",
            corner_radius=30, command=self._start_queue, width=820
        )
        self.dl_btn.pack(pady=(16, 0))

        # ── Queue overall status
        self.queue_status_lbl = ctk.CTkLabel(inner, text="",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"), text_color="#FF8FAB")
        self.queue_status_lbl.pack(pady=(8, 0))

        # ── Progress bar
        self.progress = ctk.CTkProgressBar(inner, fg_color="#FFE0E8", progress_color="#FF8FAB", corner_radius=10, height=16, width=820)
        self.progress.set(0)
        self.progress.pack(pady=(6, 0))

        # ── Per-video status
        self.status_lbl = ctk.CTkLabel(inner, text="",
            font=ctk.CTkFont(family="Georgia", size=13), text_color="#FF8FAB")
        self.status_lbl.pack(pady=(4, 0))

        # ── Log box
        self.log_box = ctk.CTkTextbox(
            inner, height=160, width=820,
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color="#FFF0F4", border_color="#FFB3C6", border_width=1,
            corner_radius=12, text_color="#555", wrap="word"
        )
        self.log_box.pack(pady=(10, 0))
        self.log_box.configure(state="disabled")

        # ── Footer
        ctk.CTkLabel(inner, text="made with 🐾 love",
            font=ctk.CTkFont(family="Georgia", size=12), text_color="#FFB3C6").pack(pady=(12, 16))

    # ── Queue management ──────────────────────────────────────────────────────
    def _add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a URL first! 🐾")
            return
        self.queue.append(url)
        self.url_entry.delete(0, "end")
        self._refresh_queue_box()
        self._log(f"➕ Added to queue: {url}")

    def _clear_queue(self):
        if self.is_downloading:
            messagebox.showwarning("Downloading", "Can't clear queue while downloading! 🐾")
            return
        self.queue.clear()
        self._refresh_queue_box()
        self._log("🗑 Queue cleared")

    def _refresh_queue_box(self):
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")
        if not self.queue:
            self.queue_box.insert("end", "Queue is empty — add URLs above! 🐾\n")
        else:
            for i, url in enumerate(self.queue, 1):
                short = url if len(url) <= 60 else url[:57] + "..."
                self.queue_box.insert("end", f"{i}. {short}\n")
        self.queue_box.configure(state="disabled")

    # ── Download flow ─────────────────────────────────────────────────────────
    def _start_queue(self):
        # If nothing in queue, treat the URL bar as a quick single download
        url = self.url_entry.get().strip()
        if not self.queue and not url:
            messagebox.showwarning("Empty Queue", "Add at least one URL to the queue or paste a URL! 🐾")
            return
        if url and url not in self.queue:
            self.queue.append(url)
            self.url_entry.delete(0, "end")
            self._refresh_queue_box()

        self.is_downloading = True
        self.dl_btn.configure(state="disabled", text="Downloading...")
        threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        total = len(self.queue)
        completed = 0

        while self.queue:
            url = self.queue.pop(0)
            self._refresh_queue_box()
            completed_so_far = completed
            self.queue_status_lbl.configure(
                text=f"🐾 Video {completed_so_far + 1} of {total}"
            )
            self._log(f"\n{'─'*40}")
            self._log(f"📥 Starting ({completed_so_far + 1}/{total}): {url}")
            self.progress.set(0)

            success = self._download_one(url)
            if success:
                completed += 1

        # All done!
        self.queue_status_lbl.configure(text=f"✅ All done! {completed}/{total} downloaded 🐾")
        self._set_status("✅ Queue complete!", color="#4CAF50")
        self._log(f"\n🎉 Finished! {completed}/{total} videos downloaded successfully.")
        self.dl_btn.configure(state="normal", text="⬇   Download All")
        self.is_downloading = False

    def _download_one(self, url: str) -> bool:
        self._set_status("🐾 Fetching info...")

        def progress_hook(d):
            if d["status"] == "downloading":
                pct = d.get("_percent_str", "?").strip().replace("%", "")
                speed = d.get("_speed_str", "").strip()
                eta = d.get("_eta_str", "").strip()
                try:
                    self.progress.set(float(pct) / 100)
                    self._set_status(f"⬇  {pct}%  •  {speed}  •  ETA {eta}")
                except Exception:
                    pass
            elif d["status"] == "finished":
                self.progress.set(0.95)
                self._set_status("⚙️ Merging... please wait!", color="#FF8FAB")
                self._log("⚙️ Merging video + audio with ffmpeg...")

        is_playlist = self.playlist_var.get() == "full"

        ydl_opts = {
            # Folder ONLY when URL is actually a playlist, never for individual URLs
            "outtmpl": os.path.join(self.download_path, "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")
                       if (is_playlist and ("playlist" in url or "list=" in url)) else
                       os.path.join(self.download_path, "%(uploader)s - %(title)s.%(ext)s"),
            "format": "bestvideo[protocol!=m3u8][protocol!=m3u8_native]+bestaudio[protocol!=m3u8][protocol!=m3u8_native]/bestvideo+bestaudio/best" if any(x in url for x in ["pinterest", "pin.it"]) else "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": not is_playlist,
            # ── Speed optimizations 🚀
            # Pinterest/HLS streams break with concurrent downloads
            "concurrent_fragment_downloads": 1 if any(x in url for x in ["pinterest", "pin.it"]) else 4,
            "buffersize": 1024 * 16,
            "http_chunk_size": 1024 * 1024 * 10,
            "retries": 10,
            "fragment_retries": 10,
            "keepvideo": False,
            "keep_fragments": False,
            # ── FFmpeg: copy video (fast!) + convert audio to AAC only
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
            ],
            "postprocessor_args": {
                "default": [
                    "-vcodec", "copy",
                    "-acodec", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                ]
            },
            # Use Edge cookies if available, skip silently if Edge is open/unavailable
            "cookiesfrombrowser": ("edge", None, None, None) if self._edge_cookies_available() else None,
            "progress_hooks": [progress_hook],
            "quiet": False,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # handle playlist info
                if "entries" in info:
                    count = len(list(info["entries"]))
                    self._log(f"✅ Playlist done! {count} videos saved to: {self.download_path}")
                else:
                    title = info.get("title", "video")
                    self._log(f"✅ Done: {title}")
                self.progress.set(1.0)
                return True
        except Exception as e:
            self._set_status("❌ Failed", color="#e53935")
            self._log(f"❌ Error: {str(e)}")
            return False

    def _edge_cookies_available(self) -> bool:
        """Check if Edge cookies can be accessed (Edge must be closed)"""
        import glob
        edge_cookie_paths = glob.glob(os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\Edge\User Data\*\Cookies"
        ))
        if not edge_cookie_paths:
            return False
        # Try to open the cookie file — if Edge is open it will be locked
        for path in edge_cookie_paths:
            try:
                with open(path, 'rb'):
                    return True
            except (PermissionError, OSError):
                return False
        return False

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _paste_url(self):
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
        except Exception:
            pass

    def _pick_directory(self):
        path = filedialog.askdirectory(initialdir=self.download_path, title="Choose download folder")
        if path:
            self.download_path = path
            self.path_label.configure(text=path)
            config["download_path"] = path
            save_config(config)
            self._log("📁 Save location updated: " + path)

    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, msg: str, color: str = "#FF8FAB"):
        self.status_lbl.configure(text=msg, text_color=color)

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PawLoaderApp()
    app.mainloop()