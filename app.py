import streamlit as st
import yt_dlp
import os
import threading
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────────────────
DOWNLOAD_ROOT = "downloads"
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

st.set_page_config(
    page_title="PawLoader 🐾",
    page_icon="🐾",
    layout="centered"
)

# ─── Session State ─────────────────────────────────────────────────────────
if "queue" not in st.session_state:
    st.session_state.queue = []

if "logs" not in st.session_state:
    st.session_state.logs = ""

if "downloading" not in st.session_state:
    st.session_state.downloading = False


# ─── UI ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style='color:#FF6B8A;'>🐾 PawLoader</h1>
    <p style='color:#888;'>TikTok · Instagram · YouTube · Playlists</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# ─── URL Input ─────────────────────────────────────────────────────────────
url = st.text_input("🔗 Paste video or playlist URL")

playlist_mode = st.radio(
    "Playlist Mode",
    ["Full playlist", "Single video only"],
    horizontal=True
)

if st.button("➕ Add to Queue"):
    if url:
        st.session_state.queue.append(url)
        st.success("Added to queue 🐾")
    else:
        st.warning("Paste a URL first")

# ─── Queue Display ─────────────────────────────────────────────────────────
st.subheader("📋 Download Queue")

if st.session_state.queue:
    for i, q in enumerate(st.session_state.queue, 1):
        st.write(f"{i}. {q}")
else:
    st.info("Queue is empty")

if st.button("🗑 Clear Queue"):
    st.session_state.queue.clear()

# ─── Download Button ───────────────────────────────────────────────────────
st.divider()

progress_bar = st.progress(0)
status_text = st.empty()

def log(msg):
    st.session_state.logs += msg + "\n"

def download_video(url, index, total):
    is_playlist = playlist_mode == "Full playlist"

    folder = os.path.join(
        DOWNLOAD_ROOT,
        datetime.now().strftime("%Y-%m-%d")
    )
    os.makedirs(folder, exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            try:
                pct = float(d["_percent_str"].replace("%", "").strip())
                progress_bar.progress(int(pct))
                status_text.info(
                    f"⬇ {pct:.1f}% | {d.get('_speed_str','')} | ETA {d.get('_eta_str','')}"
                )
            except:
                pass

        if d["status"] == "finished":
            status_text.warning("⚙️ Merging...")

    ydl_opts = {
        "outtmpl": f"{folder}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": not is_playlist,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
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
        download_video(url, i, total)
        progress_bar.progress(0)

    st.session_state.queue.clear()
    st.session_state.downloading = False
    status_text.success("🎉 All downloads completed!")

if st.button("⬇ Download All", disabled=st.session_state.downloading):
    if st.session_state.queue:
        start_download()
    else:
        st.warning("Queue is empty")

# ─── Logs ──────────────────────────────────────────────────────────────────
st.subheader("🧾 Logs")
st.text_area(
    "",
    st.session_state.logs,
    height=200
)

st.caption("made with 🐾 love")
