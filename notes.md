# Notes

Pipeline: Spotify playlist -> track list -> YouTube search+match (yt-dlp,
no third-party spotify-to-youtube converter needed) -> download+extract mp3
-> ID3 tag -> burn.

Tested and confirmed working against a real playlist (50 tracks) and a
real download/tag round trip.

## Spotify auth

Spotify locked down the Client Credentials (app-only) flow for playlist
endpoints in a late-2024 policy change - even public playlists you own now
return 401 without it. Using SpotifyOAuth (user login flow, one-time
browser approval, token cached at .spotify_cache, gitignored) instead.

Also: the playlist item response shape changed - track data lives under
`entry["item"]` instead of `entry["track"]`, with an `episode` bool to
filter out podcast episodes mixed into a playlist.

## Running it

1. Create a Spotify Developer app, put the client id/secret in
   config.local.json (gitignored, copy from config.local.example.json).
2. `python main.py <playlist_url> --out downloads --burn none` first,
   check the downloads before burning.
3. `--burn data` for a data disc (IMAPI2), `--burn audio` for a real audio
   CD (IMAPI2 track-at-once, writes CD-DA directly, no Explorer staging
   step needed).

## CD burning gotchas

- Audio CD burning went through IMAPI2's MsftDiscFormat2TrackAtOnce.
  Needs raw 16-bit 44.1kHz stereo PCM per track, padded to a whole number
  of 2352-byte sectors.
- A partially written or previously failed CD-R will report as
  "unsupported media" - only a genuinely blank disc works. This cost three
  CD-Rs before that was clear.
- Always run with --dry-run first: it converts every track, adds up
  sectors, and reports whether the playlist fits before anything touches
  the disc.

## Matching gotchas

matcher.py scores YouTube search results by duration difference plus a
keyword penalty (live, remix, cover, reaction, sped up, 8d audio, karaoke,
instrumental) unless that word is also in the actual track title. Only
tested on a handful of playlists - deluxe editions, remasters, and
orchestral covers that are the "real" pick can still throw it off.

## Ideas not built yet

Hitster offline: Hitster's physical cards show a Spotify QR code that
streams the track, which needs internet. An offline version would reuse
spotify_client.py / matcher.py / downloader.py as-is: scan the QR/link off
a card, download+index the audio, push the built library to a phone for
offline play. Not designed yet: the scanning mechanism, the on-phone
player, or the index file format.
