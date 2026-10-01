from pathlib import Path
import os, sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
print("=" * 60); print("MovieFlix setup check"); print("=" * 60)
print("Project:", ROOT)

engine = os.getenv("DB_ENGINE", "sqlite").strip().lower()
print("DB_ENGINE:", engine)

if engine != "mysql":
    import db
    print("Sample movies loaded:", db.count())
    print("Setup check passed. Run: python app.py")
    sys.exit(0)

print(".env exists:", (ROOT / ".env").exists())
token = os.getenv("TMDB_ACCESS_TOKEN", "").strip()
key = os.getenv("TMDB_API_KEY", "").strip()
print("TMDB v4 configured:", bool(token)); print("TMDB v3 configured:", bool(key))
print("TMDB credential configured:", bool(token or key))
if not (token or key):
    print("ACTION: copy .env.example to .env and add one TMDB credential.")
    sys.exit(1)
try:
    import tmdb_client
    d = tmdb_client.test_connection(); print("TMDB connection: OK ->", d.get("title"))
except Exception as e:
    print("TMDB connection: FAILED ->", e); sys.exit(2)
try:
    import db
    db.server().close(); print("MySQL connection: OK")
except Exception as e:
    print("MySQL connection: FAILED ->", e); sys.exit(3)
print("Setup check passed.")
