"""Production backend: MySQL + TMDB data populated by scripts/fetch_movies.py.
Same function signatures as db_sqlite.py."""
import mysql.connector
import config
from db_common import COLUMNS, clean as _clean


def _connect(with_db=True):
    kw = {"host": config.MYSQL_HOST, "port": config.MYSQL_PORT,
          "user": config.MYSQL_USER, "password": config.MYSQL_PASSWORD,
          "charset": "utf8mb4", "use_pure": True}
    if with_db:
        kw["database"] = config.MYSQL_DATABASE
    return mysql.connector.connect(**kw)


def server():
    return _connect(False)


def conn():
    return _connect(True)


def init_db():
    c = server()
    q = c.cursor()
    q.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` "
              "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    q.close(); c.close()
    c = conn()
    q = c.cursor()
    q.execute("""CREATE TABLE IF NOT EXISTS movies(
        id INT PRIMARY KEY, title VARCHAR(500), original_title VARCHAR(500), overview TEXT,
        release_date DATE NULL, vote_average DECIMAL(4,2), vote_count INT, popularity DECIMAL(12,3),
        poster_path VARCHAR(500), poster_url VARCHAR(1000), backdrop_path VARCHAR(500),
        backdrop_url VARCHAR(1000), genres VARCHAR(1000), keywords TEXT, language VARCHAR(20),
        adult BOOLEAN, INDEX idx_pop(popularity), INDEX idx_rel(release_date))
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    q.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) NOT NULL UNIQUE,
        email VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_username(username),
        INDEX idx_email(email))
        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    c.commit(); q.close(); c.close()


def upsert(rows):
    init_db()
    c = conn()
    q = c.cursor()
    cols = ",".join(COLUMNS)
    marks = ",".join(["%s"] * len(COLUMNS))
    upd = ",".join(f"{k}=VALUES({k})" for k in COLUMNS if k != "id")
    sql = f"INSERT INTO movies({cols}) VALUES({marks}) ON DUPLICATE KEY UPDATE {upd}"
    data = [tuple(m.get(k) for k in COLUMNS) for m in rows]
    q.executemany(sql, data)
    c.commit(); q.close(); c.close()


def _fetch(sql, params=(), one_row=False):
    c = conn()
    q = c.cursor(dictionary=True)
    q.execute(sql, params)
    res = q.fetchone() if one_row else q.fetchall()
    q.close(); c.close()
    if one_row:
        return _clean(res) if res else None
    return [_clean(r) for r in res]


def all_movies():
    return _fetch("SELECT * FROM movies WHERE adult=0 ORDER BY popularity DESC, vote_count DESC")


def one(mid):
    return _fetch("SELECT * FROM movies WHERE id=%s", (int(mid),), one_row=True)


def count():
    c = conn()
    q = c.cursor()
    q.execute("SELECT COUNT(*) FROM movies")
    n = q.fetchone()[0]
    q.close(); c.close()
    return n


def has_real_posters():
    """True once fetch_movies.py has populated real TMDB posters."""
    try:
        c = conn()
        q = c.cursor()
        q.execute("SELECT COUNT(*) FROM movies WHERE poster_url LIKE 'http%'")
        n = q.fetchone()[0]
        q.close(); c.close()
        return n > 0
    except Exception:
        return False


def by_ids(ids):
    ids = [int(i) for i in ids]
    if not ids:
        return []
    format_strings = ",".join(["%s"] * len(ids))
    rows = {m["id"]: m for m in _fetch(f"SELECT * FROM movies WHERE id IN ({format_strings}) AND adult=0", ids)}
    return [rows[i] for i in ids if i in rows]


def top(kind="popular", limit=20, genre_id=None, need_backdrop=False, exclude=None):
    where, params = ["adult=0"], []
    if genre_id:
        where.append("FIND_IN_SET(%s, genres)"); params.append(str(genre_id))
    if need_backdrop:
        where.append("backdrop_url LIKE 'http%'")
    if exclude:
        where.append("id <> %s"); params.append(int(exclude))
    if kind == "rated":
        where.append("vote_count >= 200"); order = "vote_average DESC, vote_count DESC"
    elif kind == "latest":
        where.append("release_date IS NOT NULL AND release_date <= CURDATE() AND vote_count >= 20")
        order = "release_date DESC"
    else:
        order = "popularity DESC"
    sql = f"SELECT * FROM movies WHERE {' AND '.join(where)} ORDER BY {order} LIMIT %s"
    return _fetch(sql, (*params, int(limit)))


def search(text, limit=60):
    text = (text or "").strip()
    if not text:
        return top("popular", limit)
    like = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    sql = ("SELECT * FROM movies WHERE adult=0 AND (title LIKE %s OR original_title LIKE %s OR overview LIKE %s) "
           "ORDER BY (title LIKE %s) DESC, popularity DESC LIMIT %s")
    return _fetch(sql, (like, like, like, like, int(limit)))


def create_user(username, email, password_hash):
    init_db()
    c = conn()
    q = c.cursor(dictionary=True)
    try:
        q.execute(
            "INSERT INTO users(username, email, password_hash) VALUES(%s, %s, %s)",
            (username.strip(), email.strip().lower(), password_hash)
        )
        c.commit()
        uid = q.lastrowid
        q.execute("SELECT id, username, email, created_at FROM users WHERE id=%s", (uid,))
        user = q.fetchone()
        q.close(); c.close()
        return dict(user) if user else None
    except Exception:
        q.close(); c.close()
        return None


def get_user_by_email(email):
    init_db()
    c = conn()
    q = c.cursor(dictionary=True)
    q.execute("SELECT * FROM users WHERE email=%s", (email.strip().lower(),))
    user = q.fetchone()
    q.close(); c.close()
    return dict(user) if user else None


def get_user_by_username(username):
    init_db()
    c = conn()
    q = c.cursor(dictionary=True)
    q.execute("SELECT * FROM users WHERE username=%s", (username.strip(),))
    user = q.fetchone()
    q.close(); c.close()
    return dict(user) if user else None


def get_user_by_id(uid):
    if not uid:
        return None
    init_db()
    c = conn()
    q = c.cursor(dictionary=True)
    q.execute("SELECT id, username, email, created_at FROM users WHERE id=%s", (int(uid),))
    user = q.fetchone()
    q.close(); c.close()
    return dict(user) if user else None
