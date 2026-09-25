import re
from pathlib import Path

from mutagen.mp3 import MP3

NAME_PATTERN = re.compile(r"^\d+ - (.+)\.mp3$")


def _list_tracks(out_dir: Path) -> list[Path]:
    return sorted(out_dir.glob("*.mp3"))


def _renumber(tracks: list[Path]) -> None:
    for i, path in enumerate(tracks, start=1):
        match = NAME_PATTERN.match(path.name)
        rest = match.group(1) if match else path.stem
        new_path = path.with_name(f"{i:02d} - {rest}.mp3")
        if new_path != path:
            path.rename(new_path)


def print_tracklist(out_dir: Path) -> None:
    tracks = _list_tracks(out_dir)
    total_seconds = 0
    for i, path in enumerate(tracks, start=1):
        length = MP3(path).info.length
        total_seconds += length
        match = NAME_PATTERN.match(path.name)
        name = match.group(1) if match else path.stem
        print(f"{i:2d}. {name}  ({length / 60:.1f} min)")
    print(f"Total: {total_seconds / 60:.1f} min")


def remove_track(out_dir: Path, number: int) -> None:
    tracks = _list_tracks(out_dir)
    if number < 1 or number > len(tracks):
        raise ValueError(f"No track {number} (there are {len(tracks)}).")
    removed = tracks.pop(number - 1)
    removed.unlink()
    _renumber(tracks)


def interactive_trim(out_dir: Path) -> None:
    while True:
        print_tracklist(out_dir)
        choice = input("Remove track number (blank to stop): ").strip()
        if not choice:
            return
        remove_track(out_dir, int(choice))
