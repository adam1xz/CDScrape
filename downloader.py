import re
from pathlib import Path

import yt_dlp

from spotify_client import Track


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def download_track(track: Track, video_url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = sanitize_filename(f"{track.track_number:02d} - {track.artist} - {track.title}")
    out_template = str(out_dir / f"{stem}.%(ext)s")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
        ],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([video_url])

    result = out_dir / f"{stem}.mp3"
    if not result.exists():
        raise RuntimeError(f"Expected output file not found: {result}")
    return result
