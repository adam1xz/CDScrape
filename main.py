import argparse
import sys
from pathlib import Path

from downloader import download_track
from matcher import find_best_match, find_existing_match
from spotify_client import get_playlist_tracks
from tagger import tag_mp3
from trimmer import interactive_trim

import burner


def fetch_and_download(playlist_url: str, out_dir: Path) -> list[Path]:
    tracks = get_playlist_tracks(playlist_url)
    print(f"Found {len(tracks)} tracks in playlist.")

    downloaded: list[Path] = []
    for track in tracks:
        print(f"[{track.track_number:02d}/{len(tracks)}] {track.artist} - {track.title}")

        existing = find_existing_match(track, out_dir)
        if existing:
            downloaded.append(existing)
            print(f"  already have it -> {existing.name}")
            continue

        match = find_best_match(track)
        if not match:
            print("  no YouTube match found, skipping")
            continue

        video_url = match.get("url") or f"https://www.youtube.com/watch?v={match['id']}"
        try:
            mp3_path = download_track(track, video_url, out_dir)
            tag_mp3(mp3_path, track)
            downloaded.append(mp3_path)
            print(f"  -> {mp3_path.name}")
        except Exception as exc:
            print(f"  failed: {exc}")

    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify playlist -> downloaded, tagged MP3s -> CD")
    parser.add_argument("playlist_url", nargs="?", help="Spotify playlist URL or URI")
    parser.add_argument("--out", default="downloads", help="Output folder for MP3s")
    parser.add_argument("--burn-only", metavar="FOLDER", help="Skip Spotify/download, burn an existing folder")
    parser.add_argument("--trim", metavar="FOLDER", help="List tracks in a folder and remove some interactively")
    parser.add_argument("--dry-run", action="store_true", help="Check the burn would fit without writing to the disc")
    parser.add_argument(
        "--burn",
        choices=["none", "data", "audio"],
        default="none",
        help="Burn mode: data disc, audio CD, or none",
    )
    args = parser.parse_args()

    if args.trim:
        interactive_trim(Path(args.trim))
        return

    if args.burn_only:
        out_dir = Path(args.burn_only)
        downloaded = sorted(out_dir.glob("*.mp3"))
        print(f"Found {len(downloaded)} mp3s in {out_dir}")
    else:
        if not args.playlist_url:
            parser.error("playlist_url is required unless --burn-only is given")
        out_dir = Path(args.out)
        downloaded = fetch_and_download(args.playlist_url, out_dir)

    if not downloaded:
        print("Nothing to burn.")
        sys.exit(1)

    if args.burn == "data":
        print("Burning data disc...")
        burner.burn_data_disc(out_dir)
        print("Done.")
    elif args.burn == "audio":
        print("Burning audio CD...")
        burner.burn_audio_cd(downloaded, dry_run=args.dry_run)
        print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
