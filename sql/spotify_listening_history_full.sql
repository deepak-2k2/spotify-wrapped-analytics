-- =====================================================================
--  SpotifyListeningHistory (Complete Table Definition)
--  Spotify Wrapped Analytics Project
--
--  This script creates the full SQL Server table used to store
--  Spotify listening history, including:
--      ✔ Track metadata
--      ✔ Artist metadata
--      ✔ Genre information
--      ✔ Playback timestamps
--      ✔ Duration
--      ✔ Album and artist image URLs (used for Power BI visuals)
--
--  Used by:
--      python/spotify_history_logger.py
--      python/backfill_album_artist_images.py
--
--  Notes:
--      - UNIQUE(TrackId, PlayedAtUtc) prevents duplicate plays.
--      - DATETIME2 is used for accurate UTC timestamps.
-- =====================================================================

-- ==============================
-- 1) Create Main Table
-- ==============================

CREATE TABLE dbo.SpotifyListeningHistory (
    Id INT IDENTITY(1,1) PRIMARY KEY,

    TrackId NVARCHAR(100) NOT NULL,
    TrackName NVARCHAR(255) NOT NULL,

    ArtistId NVARCHAR(100) NOT NULL,
    ArtistName NVARCHAR(255) NOT NULL,

    PrimaryGenre NVARCHAR(200) NULL,
    AlbumName NVARCHAR(255) NULL,

    PlayedAtUtc DATETIME2 NOT NULL,
    DurationMs INT NOT NULL,

    Source NVARCHAR(50) NULL,

    CONSTRAINT UQ_SpotifyListeningHistory UNIQUE (TrackId, PlayedAtUtc)
);

-- ==============================
-- 2) Add Image Columns
-- ==============================

ALTER TABLE dbo.SpotifyListeningHistory
ADD AlbumImageUrl  NVARCHAR(MAX),
    ArtistImageUrl NVARCHAR(MAX);
