import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LOCAL_CONFIG_PATH = PROJECT_ROOT / "config.local.json"


def _load_local_config() -> dict:
    if LOCAL_CONFIG_PATH.exists():
        return json.loads(LOCAL_CONFIG_PATH.read_text())
    return {}


def get_spotify_credentials() -> tuple[str, str]:
    local = _load_local_config()
    client_id = os.environ.get("SPOTIFY_CLIENT_ID") or local.get("spotify_client_id")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET") or local.get("spotify_client_secret")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Spotify credentials not found. Set SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET "
            "env vars, or create config.local.json (see config.local.example.json)."
        )
    return client_id, client_secret
