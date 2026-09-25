from pathlib import Path

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3

from spotify_client import Track


def tag_mp3(path: Path, track: Track) -> None:
    try:
        audio = EasyID3(path)
    except ID3NoHeaderError:
        mp3 = MP3(path)
        mp3.add_tags()
        mp3.save()
        audio = EasyID3(path)

    audio["artist"] = track.artist
    audio["title"] = track.title
    audio["album"] = track.album
    audio["tracknumber"] = str(track.track_number)
    audio.save()
