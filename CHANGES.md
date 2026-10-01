# Errors found and fixed

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | tmdb_client.py | After 3 rate-limit/5xx responses `_get()` fell out of the loop and **returned `None`**, causing a confusing `AttributeError` later | Raises `TMDBError` after the last retry; honours `Retry-After`; 401/404 fail fast |
| 2 | tmdb_client.py | `image_url('/')` produced `https://image.tmdb.org/t/p/w500/` even though the README promises a fallback | Empty / `/` / non-string paths now use the fallback |
| 3 | tmdb_client.py | A new HTTP session was created on every retry | One session per request |
| 4 | db.py | `ON DUPLICATE KEY UPDATE` skipped `original_title` and `keywords`, so re-fetching never refreshed them | All columns updated |
| 5 | db.py / app.py | Every page loaded **every movie** from MySQL, then filtered in Python | SQL queries with `LIMIT`, `LIKE`, `FIND_IN_SET`, indexes on popularity/release date |
| 6 | db.py | `all_movies()` ran `CREATE DATABASE/TABLE` on every call | `init_db()` only on write |
| 7 | db.py | `Decimal` / `date` values leaked into templates and JSON (`7.50`, date objects) | Rows normalised in `_clean()` |
| 8 | recommender.py | Pickle model re-read from disk and compared to the whole DB on every request | Model cached, reloaded only when the file changes; only the top matches are fetched |
| 9 | recommender.py | No model → empty "Recommended" section | Falls back to popular movies from the same genre |
| 10 | build_features.py | Genres were stored as TMDB ids (`28,12`) and fed to TF-IDF as meaningless numbers | Ids converted to genre names (weighted x2) |
| 11 | fetch_movies.py | `keywords` was always empty | Optional `--details` flag stores real TMDB keywords |
| 12 | app.py | Search text was lowercased before display; no 404 page; DB outage showed a raw traceback | Original text kept; friendly 404 and "Database not ready" pages |
| 13 | style.css | Global `h1,h2{margin-left:5%}` misaligned headings inside the details page | Scoped styles |
| 14 | schema.sql | Only created the database, not the table | Full schema |
| 15 | setup_check.py | Did not test MySQL | Now checks the MySQL connection too |
| 16 | tests | Only 2 trivial tests | 30 tests: retry logic, posters, recommender, every route, XSS escaping, DB-error page |

## Zero-setup demo mode (added)
The project needed a TMDB API key and a running MySQL server before it would even start, which
is a lot for an educational/classroom demo. I can't generate a real TMDB key on your behalf (it's
tied to a personal account, and a fake one just fails silently) — instead:

- `DB_ENGINE=sqlite` (new default) stores movies in a local file, no server to install.
- `demo_data.py` seeds it with 28 sample movies on first run, so `python app.py` alone shows a
  fully working site — hero slideshow, rows, search, recommendations, movie pages — with nothing
  to configure.
- `db.py` is now a thin router between `db_sqlite.py` (default) and `db_mysql.py`
  (`DB_ENGINE=mysql`, for real TMDB data); both share one row-cleaning module (`db_common.py`) and
  expose identical functions, so `app.py` / `recommender.py` don't need to know which is active.
- Hero slides no longer require a real backdrop image — movies without one get a styled colour
  gradient instead, so the slideshow still looks intentional in demo mode.

## Real posters (added)
The 28 demo movies are fictional (invented for the zero-setup demo), so there's no real poster
for them anywhere — the colored placeholder art is expected there, not a bug. Two changes:

- `README.md` corrected: `scripts/fetch_movies.py` was documented as needing MySQL, but it only
  calls `db.upsert()`, which already works against the default SQLite database. A free TMDB key
  is genuinely all that's needed to pull real movies and posters — no MySQL required.
- The app now shows an in-page notice ("Showing placeholder posters…") whenever no movie in the
  database has a real poster yet, so this isn't confusing on first run. It disappears automatically
  once `fetch_movies.py` has added real TMDB data. (`db_sqlite.has_real_posters()` /
  `db_mysql.has_real_posters()`)
