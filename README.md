# CDScrape

Takes a spotify playlist, finds each song on youtube, downloads it as mp3,
tags it, and can burn it to a cd.

### Spotify setup
1. go to https://developer.spotify.com/dashboard and make an app
2. add this redirect uri to it: http://127.0.0.1:8888/callback
3. copy config.local.example.json to config.local.json and put your
   client id and secret in it
   (or set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars)
first run opens a browser to log in, after that it's cached

### Install (windows)
need python 3 and ffmpeg in your PATH

python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

### Install (linux)
python3 -m venv .venv
.venv/bin/pip install yt-dlp spotipy mutagen

burning only works on windows (it uses IMAPI2 and pywin32), and main.py
imports the burner so on linux you'd have to remove that import first

### Run
easy way on windows: double click run.bat and answer the questions

or by hand:
python main.py <playlist url> --out myfolder --burn none

### Options
```
 playlist_url      the spotify playlist link
 --out FOLDER      where the mp3s go, default is downloads
 --burn none       just download, no burning (default)
 --burn data       burn the folder as a data disc (mp3 files on the cd)
 --burn audio      burn a real audio cd, this is the one for car players
 --dry-run         with --burn audio, converts everything and tells you if
                  it fits on the disc, doesn't write anything             
 --burn-only FOLDER  skip spotify and downloading, burn a folder you already have
 --trim FOLDER     lists the tracks in a folder and lets you remove some
                  (use it if the playlist is too long for the disc)
```
### Tips
- pls do a dry run before burning, an audio cd holds about 80 min
- use a new blank cd-r, a used or half written one gets rejected
- running it again on the same folder skips songs it already has
