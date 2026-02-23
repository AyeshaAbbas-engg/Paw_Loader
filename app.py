import streamlit as st
import yt_dlp
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# App Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PawLoader 🐾",
    page_icon="🐾",
    layout="centered"
)

DOWNLOAD_ROOT = "downloads"
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────
if "queue" not in st.session_state:
    st.session_state.queue = []

if "logs" not in st.session_state:
    st.session_state.logs = ""

if "downloading" not in st.session_state:
    st.session_state.downloading = False

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def log(msg):
    st.session_state.logs += msg + "\n"

# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="color:#FF6B8A;">🐾 PawLoader</h1>
    <p style="color:#888;">YouTube · TikTok · Instagram · Playlists</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# ─────────────────────────────────────────────────────────────
# URL Input
# ─────────────────────────────────────────────────────────────
url = st.text_input("🔗 Paste video or playlist URL")

playlist_mode = st.radio(
    "Playlist Mode",
    ["Full playlist", "Single video only"],
    horizontal=True
)

if st.button("➕ Add to Queue"):
    if url.strip():
        st.session_state.queue.append(url.strip())
        st.success("Added to queue 🐾")
    else:
        st.warning("Please paste a URL first")

# ─────────────────────────────────────────────────────────────
# Queue Display
# ─────────────────────────────────────────────────────────────
st.subheader("📋 Download Queue")

if st.session_state.queue:
    for i, q in enumerate(st.session_state.queue, 1):
        st.write(f"{i}. {q}")
else:
    st.info("Queue is empty")

if st.button("🗑 Clear Queue"):
    st.session_state.queue.clear()
    st.success("Queue cleared")

st.divider()

# ─────────────────────────────────────────────────────────────
# Download Logic
# ─────────────────────────────────────────────────────────────
progress_bar = st.progress(0)
status_text = st.empty()

def download_one(url, index, total):
    is_playlist = playlist_mode == "Full playlist"

    folder = os.path.join(
        DOWNLOAD_ROOT,
        datetime.now().strftime("%Y-%m-%d")
    )
    os.makedirs(folder, exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            try:
                percent = float(
                    d.get("_percent_str", "0%").replace("%", "").strip()
                )
                progress_bar.progress(int(percent))
                status_text.info(
                    f"⬇ {percent:.1f}% | "
                    f"{d.get('_speed_str','')} | "
                    f"ETA {d.get('_eta_str','')}"
                )
            except:
                pass

        elif d["status"] == "finished":
            status_text.warning("⚙️ Finalizing download...")

    # 🔐 NO FFMPEG REQUIRED FORMAT
    ydl_opts = {
        "outtmpl": f"{folder}/%(title)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "noplaylist": not is_playlist,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            log(f"✅ Downloaded: {url}")
            return True
    except Exception as e:
        log(f"❌ Failed: {str(e)}")
        return False

def start_download():
    st.session_state.downloading = True
    total = len(st.session_state.queue)

    for i, url in enumerate(st.session_state.queue, 1):
        status_text.info(f"🐾 Video {i} of {total}")
        download_one(url, i, total)
        progress_bar.progress(0)

    st.session_state.queue.clear()
    st.session_state.downloading = False
    status_text.success("🎉 All downloads completed!")

# ─────────────────────────────────────────────────────────────
# Download Button
# ─────────────────────────────────────────────────────────────
if st.button("⬇ Download All", disabled=st.session_state.downloading):
    if st.session_state.queue:
        start_download()
    else:
        st.warning("Queue is empty")

# ─────────────────────────────────────────────────────────────
# Logs
# ─────────────────────────────────────────────────────────────
st.subheader("🧾 Logs")
st.text_area(
    "",
    st.session_state.logs,
    height=220
)

st.caption("made with 🐾 love")
