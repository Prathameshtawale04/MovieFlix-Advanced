from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN", "").strip()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Zero-setup by default: a local SQLite file pre-seeded with sample movies.
# Set DB_ENGINE=mysql in .env once you're ready to use your own MySQL server + live TMDB data.
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
SQLITE_PATH = BASE_DIR / "data" / "movieflix.db"

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = _int("MYSQL_PORT", 3306)
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "movieflix")

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

TMDB_BASE_URL = "https://api.themoviedb.org/3"
FALLBACK_POSTER = "/static/img/poster-fallback.svg"
