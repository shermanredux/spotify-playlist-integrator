import os
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *

def load_downloaded():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def log_downloaded(name_key):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(name_key + "\n")

def check_local_folder_and_repopulate():
    downloaded = load_downloaded()

    if not os.path.exists(DOWNLOAD_DIR):
        print("he download folder doesn't exist.")
        return downloaded
    
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".mp3"):
            song_name = filename.replace(".mp3", "")
            downloaded.add(song_name)
    
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for song in downloaded:
            f.write(song + "\n")
    
    return downloaded

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-read-private"
))

try:
    playlist_data = sp.playlist(SPOTIFY_PLAYLIST_ID)
    playlist_name = playlist_data['name']
    print(f"Connected to playlist: {playlist_name}")
except Exception as e:
    print("Failed to connect to the playlist. Please check your ID and credentials.")
    print("Error:", e)
    exit(1)

def fetch_all_tracks():
    tracks = []
    results = sp.playlist_tracks(SPOTIFY_PLAYLIST_ID, limit=100, offset=0)
    tracks.extend([(item['track']['name'], item['track']['artists'][0]['name']) for item in results['items']])

    while results['next']:
        results = sp.next(results)
        tracks.extend([(item['track']['name'], item['track']['artists'][0]['name']) for item in results['items']])

    return tracks

tracks = fetch_all_tracks()

downloaded = check_local_folder_and_repopulate()

for title, artist in tracks:
    name_key = f"{title} - {artist}".strip().replace("/", "-")
    file_path = os.path.join(DOWNLOAD_DIR, name_key + ".mp3")

    if name_key in downloaded or os.path.exists(file_path):
        print(f"Already downloaded: {name_key}")
        continue

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch1:',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f"{name_key}.%(ext)s"),
        'ffmpeg_location': r'C:\ffmpeg\bin', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    print(f"Downloading: {name_key}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"{title} {artist} audio"])
        log_downloaded(name_key)
        print(f"Finished: {name_key}")
    except Exception as e:
        print(f"Failed to download {name_key}: {e}")
