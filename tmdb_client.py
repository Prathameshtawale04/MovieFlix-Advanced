import time
import requests
import config

RETRY_STATUS = (429, 500, 502, 503, 504)


class TMDBError(Exception):
    pass


def credential_mode():
    if config.TMDB_ACCESS_TOKEN:
        return "v4"
    if config.TMDB_API_KEY:
        return "v3"
    return None


def _session():
    mode = credential_mode()
    if not mode:
        raise TMDBError("No TMDB credential. Set TMDB_ACCESS_TOKEN (v4) or TMDB_API_KEY (v3) in .env.")
    s = requests.Session()
    s.headers.update({"accept": "application/json", "User-Agent": "MovieFlix/1.0"})
    if mode == "v4":
        s.headers["Authorization"] = "Bearer " + config.TMDB_ACCESS_TOKEN
    return s


def _get(endpoint, params=None, attempts=4):
    p = dict(params or {})
    if credential_mode() == "v3":
        p["api_key"] = config.TMDB_API_KEY
    session = _session()  # one session for all retries
    last = "unknown error"
    for attempt in range(attempts):
        try:
            r = session.get(config.TMDB_BASE_URL + endpoint, params=p, timeout=30)
        except requests.RequestException as e:
            last = f"TMDB connection failed: {e}"
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200:
            return r.json()
        try:
            detail = r.json()
        except ValueError:
            detail = r.text
        last = f"TMDB HTTP {r.status_code}: {detail}"
        if r.status_code in RETRY_STATUS:
            try:
                wait = float(r.headers.get("Retry-After", 2 ** attempt))
            except (TypeError, ValueError):
                wait = 2 ** attempt
            time.sleep(min(wait, 10))
            continue
        raise TMDBError(last)  # 401/404/... will not fix themselves
    raise TMDBError(last)  # all retries used (previously this silently returned None)


def test_connection():
    return _get("/movie/550")


def discover_movies(page=1):
    return _get("/discover/movie", {"page": page, "sort_by": "popularity.desc",
                                    "include_adult": "false", "include_video": "false",
                                    "language": "en-US"})


def search_movies(q, page=1):
    return _get("/search/movie", {"query": q, "page": page, "include_adult": "false", "language": "en-US"})


def movie_details(mid, with_keywords=False):
    params = {"language": "en-US"}
    if with_keywords:
        params["append_to_response"] = "keywords"
    return _get(f"/movie/{int(mid)}", params)


def image_url(path, size="w500"):
    """Full TMDB image URL, or the fallback poster (posters) / '' (other sizes)
    when the path is missing, empty, '/' or otherwise unusable."""
    ok = isinstance(path, str) and path.strip().startswith("/") and len(path.strip()) > 1
    if not ok:
        return config.FALLBACK_POSTER if size == "w500" else ""
    return f"https://image.tmdb.org/t/p/{size}{path.strip()}"


if __name__ == "__main__":
    print("Project:", config.BASE_DIR)
    print(".env:", (config.BASE_DIR / ".env").exists())
    print("Credential mode:", credential_mode() or "NONE")
    if config.TMDB_ACCESS_TOKEN:
        print("v4 token format:", config.TMDB_ACCESS_TOKEN.startswith("eyJ"), "length:", len(config.TMDB_ACCESS_TOKEN))
    try:
        print("TMDB connection: SUCCESS ->", test_connection().get("title"))
    except TMDBError as e:
        print("TMDB connection: FAILED ->", e)
