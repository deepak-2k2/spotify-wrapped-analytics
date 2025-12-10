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

SCOPE = "user-read-recently-played"  # any scope that allows auth is fine

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_TRUSTED = os.getenv("SQL_TRUSTED", "true").lower() == "true"
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

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
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        )
    )


# ================== MAIN BACKFILL ==================

def backfill_images():
    conn = get_sql_connection()
    cursor = conn.cursor()

    # 1) Get all distinct tracks that are missing album or artist image
    sql_select = """
        SELECT DISTINCT TrackId, TrackName, ArtistId
        FROM dbo.SpotifyListeningHistory
        WHERE TrackId IS NOT NULL
          AND (AlbumImageUrl IS NULL OR ArtistImageUrl IS NULL)
    """
    cursor.execute(sql_select)
    rows = cursor.fetchall()

    print(f"Found {len(rows)} tracks to backfill.")

    if not rows:
        conn.close()
        print("Nothing to backfill.")
        return

    sp = get_spotify_client()

    for track_id, track_name, artist_id in rows:
        print(f"\nProcessing TrackId={track_id} | {track_name}")

        album_image_url = None
        artist_image_url = None

        # --- Fetch track info (album image) ---
        try:
            track_obj = sp.track(track_id)
            album = track_obj.get("album", {})
            images = album.get("images", [])
            if images:
                album_image_url = images[0]["url"]
        except Exception as e:
            print(f"  Error fetching track {track_id}: {e}")

        # --- Fetch artist info (artist image) ---
        if artist_id:
            try:
                artist_obj = sp.artist(artist_id)
                artist_images = artist_obj.get("images", [])
                if artist_images:
                    artist_image_url = artist_images[0]["url"]
            except Exception as e:
                print(f"  Error fetching artist {artist_id}: {e}")

        if not album_image_url and not artist_image_url:
            print("  No images found, skipping update.")
            continue

        # 2) Update ALL rows for this TrackId
        sql_update = """
            UPDATE dbo.SpotifyListeningHistory
            SET
                AlbumImageUrl = COALESCE(AlbumImageUrl, ?),
                ArtistImageUrl = COALESCE(ArtistImageUrl, ?)
            WHERE TrackId = ?
        """

        cursor.execute(sql_update, (album_image_url, artist_image_url, track_id))
        print(f"  Updated rows for track: {track_name}")

    conn.commit()
    conn.close()
    print("\nBackfill complete!")


if __name__ == "__main__":
    backfill_images()
