import time
import datetime
import os
import pyodbc
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# ================== LOAD ENV VARIABLES ==================

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

SCOPE = "user-read-recently-played"

SQL_SERVER = os.getenv("SQL_SERVER")          # e.g. localhost\SQLEXPRESS
SQL_DATABASE = os.getenv("SQL_DATABASE")      # e.g. DB1
SQL_TRUSTED = os.getenv("SQL_TRUSTED", "true").lower() == "true"

SQL_USER = os.getenv("SQL_USER")              # used only if SQL_TRUSTED=false
SQL_PASSWORD = os.getenv("SQL_PASSWORD")      # used only if SQL_TRUSTED=false

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

# ================== VALIDATION ==================

missing = []
if not CLIENT_ID:
    missing.append("SPOTIFY_CLIENT_ID")
if not CLIENT_SECRET:
    missing.append("SPOTIFY_CLIENT_SECRET")
if not SQL_SERVER:
    missing.append("SQL_SERVER")
if not SQL_DATABASE:
    missing.append("SQL_DATABASE")

if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}. "
        "Set them in your .env file."
    )

if not SQL_TRUSTED and (not SQL_USER or not SQL_PASSWORD):
    raise RuntimeError(
        "SQL_TRUSTED is false, but SQL_USER or SQL_PASSWORD is missing. "
        "Set SQL_USER and SQL_PASSWORD in your .env file."
    )


# ================== HELPERS ==================

def get_sql_connection():
    """
    Create a SQL Server connection using either Windows auth (trusted)
    or SQL username/password auth based on env settings.
    """
    if SQL_TRUSTED:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            "Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            f"UID={SQL_USER};PWD={SQL_PASSWORD};"
        )
    return pyodbc.connect(conn_str)


def get_spotify_client():
    """
    Create an authenticated Spotify client using OAuth.
    """
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        )
    )


def parse_spotify_ts(ts: str) -> datetime.datetime:
    """
    Convert Spotify timestamp like '2025-12-03T09:12:34.567Z'
    to a timezone-aware UTC datetime, then make it naive (no tzinfo) for SQL.
    """
    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)


# ================== MAIN SYNC ==================

def sync_recently_played(sp, conn):
    """
    Pull Spotify 'recently played' tracks and insert any new plays into SQL,
    including album + artist image URLs.
    """
    print("Fetching recently played...", flush=True)
    results = sp.current_user_recently_played(limit=50)
    items = results.get("items", [])

    if not items:
        print("No items returned from Spotify.", flush=True)
        return

    cursor = conn.cursor()

    # Cache artist info (genres + image) to avoid repeated API calls
    artist_cache = {}

    # Oldest -> newest
    items.sort(key=lambda x: x["played_at"])

    new_count = 0

    for item in items:
        played_at_str = item["played_at"]
        played_at_utc = parse_spotify_ts(played_at_str)

        track = item["track"]
        track_id = track["id"]
        track_name = track["name"]

        artist = track["artists"][0]
        artist_id = artist["id"]
        artist_name = artist["name"]

        album = track.get("album", {})
        album_name = album.get("name", "")

        # Album image (largest)
        album_images = album.get("images", [])
        album_image_url = album_images[0]["url"] if album_images else None

        duration_ms = track.get("duration_ms", 0)

        # Get primary genre + artist image (from cache or API)
        if artist_id in artist_cache:
            primary_genre, artist_image_url = artist_cache[artist_id]
        else:
            primary_genre = None
            artist_image_url = None
            try:
                artist_obj = sp.artist(artist_id)
                genres = artist_obj.get("genres", [])
                primary_genre = genres[0] if genres else None

                images = artist_obj.get("images", [])
                artist_image_url = images[0]["url"] if images else None
            except Exception as e:
                print("Error fetching artist info:", e, flush=True)

            artist_cache[artist_id] = (primary_genre, artist_image_url)

        # Insert only if not already present (TrackId + PlayedAtUtc)
        sql = """
        IF NOT EXISTS (
            SELECT 1
            FROM dbo.SpotifyListeningHistory
            WHERE TrackId = ? AND PlayedAtUtc = ?
        )
        INSERT INTO dbo.SpotifyListeningHistory (
            TrackId,
            TrackName,
            ArtistId,
            ArtistName,
            PrimaryGenre,
            AlbumName,
            AlbumImageUrl,
            ArtistImageUrl,
            PlayedAtUtc,
            DurationMs,
            Source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        params = (
            track_id,
            played_at_utc,     # for IF NOT EXISTS
            track_id,
            track_name,
            artist_id,
            artist_name,
            primary_genre,
            album_name,
            album_image_url,
            artist_image_url,
            played_at_utc,
            duration_ms,
            "recently_played",
        )

        cursor.execute(sql, params)

        print(
            f"Seen play: {track_name} - {artist_name} | "
            f"genre={primary_genre} | playedAt={played_at_str}",
            flush=True,
        )
        new_count += 1

    conn.commit()
    print(f"Sync complete. Processed {new_count} plays.", flush=True)


# ================== ENTRY POINT ==================

if __name__ == "__main__":
    print("Starting Spotify -> SQL history logger with images... (Ctrl + C to stop)")
    sp = get_spotify_client()
    conn = get_sql_connection()

    try:
        while True:
            try:
                sync_recently_played(sp, conn)
            except Exception as e:
                print("Unexpected error in sync loop:", e, flush=True)
            time.sleep(POLL_INTERVAL_SECONDS)
    finally:
        conn.close()
        print("SQL connection closed.")
