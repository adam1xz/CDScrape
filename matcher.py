import re
from pathlib import Path

import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from spotify_client import Track

PENALIZED_WORDS = ["live", "remix", "cover", "reaction", "sped up", "8d audio", "karaoke", "instrumental"]
SEARCH_RESULTS = 5
EXISTING_MATCH_THRESHOLD = 15


def _clean(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def _score(track: Track, cand_title: str, cand_duration: float) -> float:
    track_duration_s = track.duration_ms / 1000

    score = abs(cand_duration - track_duration_s)
    cand_clean = _clean(cand_title)

    for word in PENALIZED_WORDS:
        if word in cand_clean and word not in _clean(track.title):
            score += 30

    if _clean(track.artist) not in cand_clean:
        score += 5
    if _clean(track.title) not in cand_clean:
        score += 15

    return score


def find_best_match(track: Track) -> dict | None:
    query = f"ytsearch{SEARCH_RESULTS}:{track.artist} - {track.title} audio"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)

    entries = info.get("entries") or []
    if not entries:
        return None

    best = min(entries, key=lambda c: _score(track, c.get("title") or "", c.get("duration") or 0))
    return best


def find_existing_match(track: Track, out_dir: Path) -> Path | None:
    if not out_dir.exists():
        return None

    best_path = None
    best_score = EXISTING_MATCH_THRESHOLD
    for mp3_path in out_dir.glob("*.mp3"):
        try:
            tags = EasyID3(mp3_path)
            duration = MP3(mp3_path).info.length
        except Exception:
            continue

        artist = tags.get("artist", [""])[0]
        title = tags.get("title", [""])[0]
        score = _score(track, f"{artist} {title}", duration)
        if score < best_score:
            best_score = score
            best_path = mp3_path

    return best_path
