![Project Banner](assets/01_project_banner.png)

# 🎵 Spotify Wrapped Analytics  
A complete end-to-end data engineering and analytics project replicating **Spotify Wrapped** using:

**Python · Spotify API · SQL Server · Power BI**

This project collects your Spotify listening history, enriches it with metadata and images, stores it in SQL Server, and visualizes insights through a multi-page Power BI dashboard.

---

## 🚀 Features

### ✔ Automated Spotify Data Collection
- Fetches recently played tracks every few minutes  
- Captures track, artist, genre, album, duration, and timestamps  
- Prevents duplicate entries using SQL unique constraints  

### ✔ Image Enrichment Pipeline
- Backfills **album art** and **artist images** via Spotify API  
- Enables Spotify-styled visuals inside Power BI  

### ✔ SQL Data Storage
- Clean relational design  
- Uses `DATETIME2` for accurate UTC timestamps  
- Handles thousands of plays efficiently  

### ✔ Power BI Dashboard (4 Pages)
- **Overview Page** — Summary metrics and trends  
- **Content Insights Page** — Top artists, genres, albums  
- **Listening Habits Page** — Time-of-day & weekly patterns  
- **Wrapped Highlights Page** — Spotify Wrapped-style storytelling  

---

## 🛠️ Tech Stack

| Layer | Technologies |
|------|--------------|
| Data Source | Spotify Web API |
| ETL / Ingestion | Python, Spotipy, OAuth |
| Storage | SQL Server |
| Processing | Python scripts |
| BI & Visualization | Power BI Desktop / Service |
| Configuration | Environment variables (.env) |

---

## 📁 Folder Structure

```text
spotify-wrapped-analytics/
│
├── python/
│   ├── spotify_history_logger.py
│   └── backfill_album_artist_images.py
│
├── sql/
│   └── spotify_listening_history_full.sql
│
├── powerbi/
│   └── SpotifyWrapped.pbix
│
├── assets/
│   ├── overview_page.png
│   ├── content_insights_page.png
│   ├── listening_habits_page.png
│   ├── wrapped_highlights_page.png
│   └── project_banner.png
│
├── .env          # not committed to GitHub
├── .gitignore
└── README.md
```

---

## 🔐 Environment Variables (.env)

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

SQL_SERVER=localhost\SQLEXPRESS
SQL_DATABASE=DB1
SQL_TRUSTED=true
```

*(This file stays private and is ignored via `.gitignore`.)*

---

## 🐍 Running the Python Scripts

Install dependencies:

```bash
py -m pip install spotipy python-dotenv pyodbc
```

Run the history logger:

```bash
python python/spotify_history_logger.py
```

Run the image backfiller:

```bash
python python/backfill_album_artist_images.py
```

---

## 🗄️ SQL Setup

Run the following script in SQL Server:

```
sql/spotify_listening_history_full.sql
```

This creates the table `SpotifyListeningHistory` with fields for metadata and image URLs.

---

## 📊 Power BI Dashboard Screenshots

### **Overview Page**
![Overview](assets/02_overview_page.png)

### **Content Insights Page**
![Content Insights](assets/03_content_insights_page.png)

### **Listening Habits Page**
![Listening Habits](assets/04_listening_habits_page.png)

### **Wrapped Highlights Page**
![Wrapped Highlights](assets/05_wrapped_highlights_page.png)

---

## ⭐ Skills Demonstrated

- OAuth authentication with Spotify API  
- ETL pipeline design (Python → SQL Server → Power BI)  
- SQL schema modeling (event-based tables)  
- Data enrichment using API lookups  
- Professional Power BI dashboard design  
- GitHub project structuring & documentation  

---

## 👤 Author

**Deepak**  
GitHub: https://github.com/deepak-2k2
