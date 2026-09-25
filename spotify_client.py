from dataclasses import dataclass

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import PROJECT_ROOT, get_spotify_credentials

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private playlist-read-collaborative"


@dataclass
class Track:
    artist: str
    title: str
    album: str
    duration_ms: int
    track_number: int
    isrc: str | None


def _client() -> spotipy.Spotify:
    client_id, client_secret = get_spotify_credentials()
    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=str(PROJECT_ROOT / ".spotify_cache"),
    )
    return spotipy.Spotify(auth_manager=auth)


def get_playlist_tracks(playlist_url: str) -> list[Track]:
    sp = _client()
    results = sp.playlist_items(playlist_url, additional_types=["track"])
    tracks: list[Track] = []
    track_number = 1
    while results:
        for entry in results["items"]:
            t = entry.get("item")
            if not t or t.get("episode"):
                continue
            tracks.append(
                Track(
                    artist=t["artists"][0]["name"] if t["artists"] else "Unknown Artist",
                    title=t["name"],
                    album=t["album"]["name"] if t.get("album") else "",
                    duration_ms=t["duration_ms"],
                    track_number=track_number,
                    isrc=t.get("external_ids", {}).get("isrc"),
                )
            )
            track_number += 1
        results = sp.next(results) if results.get("next") else None
    return tracks
