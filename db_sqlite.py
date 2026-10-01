"""Zero-setup backend: a local SQLite file, pre-seeded with sample movies from demo_data.py.
Same function signatures as db_mysql.py so app.py / recommender.py don't need to know which is active."""
import sqlite3
import config
from db_common import COLUMNS, clean as _clean

config.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    c = sqlite3.connect(config.SQLITE_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    c = _connect()
    c.execute("""CREATE TABLE IF NOT EXISTS movies(
        id INTEGER PRIMARY KEY, title TEXT, original_title TEXT, overview TEXT,
        release_date TEXT, vote_average REAL, vote_count INTEGER, popularity REAL,
        poster_path TEXT, poster_url TEXT, backdrop_path TEXT, backdrop_url TEXT,
        genres TEXT, keywords TEXT, language TEXT, adult INTEGER)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pop ON movies(popularity)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rel ON movies(release_date)")

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    c.commit()

    if c.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 0:
        c.close()
        from demo_data import MOVIES
        upsert(MOVIES)  # first run: seed with the built-in sample dataset
        return
    c.close()


def upsert(rows):
    c = _connect()
    c.execute("""CREATE TABLE IF NOT EXISTS movies(
        id INTEGER PRIMARY KEY, title TEXT, original_title TEXT, overview TEXT,
        release_date TEXT, vote_average REAL, vote_count INTEGER, popularity REAL,
        poster_path TEXT, poster_url TEXT, backdrop_path TEXT, backdrop_url TEXT,
        genres TEXT, keywords TEXT, language TEXT, adult INTEGER)""")
    cols = ",".join(COLUMNS)
    marks = ",".join(["?"] * len(COLUMNS))
    upd = ",".join(f"{k}=excluded.{k}" for k in COLUMNS if k != "id")
    sql = f"INSERT INTO movies({cols}) VALUES({marks}) ON CONFLICT(id) DO UPDATE SET {upd}"
    c.executemany(sql, [tuple(m.get(k) for k in COLUMNS) for m in rows])
    c.commit(); c.close()


def _fetch(sql, params=(), one_row=False):
    init_db()
    c = _connect()
    cur = c.execute(sql, params)
    res = cur.fetchone() if one_row else cur.fetchall()
    c.close()
    if one_row:
        return _clean(dict(res)) if res else None
    return [_clean(dict(r)) for r in res]


def all_movies():
    return _fetch("SELECT * FROM movies WHERE adult=0 ORDER BY popularity DESC, vote_count DESC")


def one(mid):
    return _fetch("SELECT * FROM movies WHERE id=?", (int(mid),), one_row=True)


def count():
    init_db()
    c = _connect()
    n = c.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    c.close()
    return n


def has_real_posters():
    """True once at least one movie has a real (TMDB) poster, i.e. fetch_movies.py has been run."""
    init_db()
    c = _connect()
    n = c.execute("SELECT COUNT(*) FROM movies WHERE poster_url LIKE 'http%'").fetchone()[0]
    c.close()
    return n > 0


def by_ids(ids):
    ids = [int(i) for i in ids]
    if not ids:
        return []
    marks = ",".join(["?"] * len(ids))
    rows = {m["id"]: m for m in _fetch(f"SELECT * FROM movies WHERE id IN ({marks}) AND adult=0", ids)}
    return [rows[i] for i in ids if i in rows]  # keep the requested order


def top(kind="popular", limit=20, genre_id=None, need_backdrop=False, exclude=None):
    """kind: popular | rated | latest"""
    where, params = ["adult=0"], []
    if genre_id:
        where.append("(',' || genres || ',') LIKE ?"); params.append(f"%,{int(genre_id)},%")
    if need_backdrop:
        where.append("backdrop_url LIKE 'http%'")
    if exclude:
        where.append("id <> ?"); params.append(int(exclude))
    if kind == "rated":
        where.append("vote_count >= 200"); order = "vote_average DESC, vote_count DESC"
    elif kind == "latest":
        where.append("release_date IS NOT NULL AND release_date <= date('now') AND vote_count >= 20")
        order = "release_date DESC"
    else:
        order = "popularity DESC"
    sql = f"SELECT * FROM movies WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ?"
    return _fetch(sql, (*params, int(limit)))


def search(text, limit=60):
    text = (text or "").strip()
    if not text:
        return top("popular", limit)
    like = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    sql = ("SELECT * FROM movies WHERE adult=0 AND "
           "(title LIKE ? ESCAPE '\\' OR original_title LIKE ? ESCAPE '\\' OR overview LIKE ? ESCAPE '\\') "
           "ORDER BY (title LIKE ? ESCAPE '\\') DESC, popularity DESC LIMIT ?")
    return _fetch(sql, (like, like, like, like, int(limit)))


def create_user(username, email, password_hash):
    init_db()
    c = _connect()
    try:
        cur = c.execute(
            "INSERT INTO users(username, email, password_hash) VALUES(?, ?, ?)",
            (username.strip(), email.strip().lower(), password_hash)
        )
        c.commit()
        uid = cur.lastrowid
        user = c.execute("SELECT id, username, email, created_at FROM users WHERE id=?", (uid,)).fetchone()
        c.close()
        return dict(user) if user else None
    except Exception:
        c.close()
        return None


def get_user_by_email(email):
    init_db()
    c = _connect()
    row = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    c.close()
    return dict(row) if row else None


def get_user_by_username(username):
    init_db()
    c = _connect()
    row = c.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    c.close()
    return dict(row) if row else None


def get_user_by_id(uid):
    if not uid:
        return None
    init_db()
    c = _connect()
    row = c.execute("SELECT id, username, email, created_at FROM users WHERE id=?", (int(uid),)).fetchone()
    c.close()
    return dict(row) if row else None
