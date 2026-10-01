# MovieFlix — 5-Week Project (fixed + scroll-driven UI + zero-setup demo)

Flask + TMDB + TF-IDF content-based recommendations, with a cinematic scroll-driven front end.

## Run it right now — no API key, no database setup
```powershell
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`. That's it. It runs on a local SQLite file pre-seeded with
28 sample movies (`demo_data.py`), so there's nothing to configure for class/demo purposes.

## Switch to real TMDB posters & movies (optional)
Get a free TMDB key at https://www.themoviedb.org/settings/api (takes under a minute — I can't
generate one for you, it's tied to a personal TMDB account, and I'm not able to source real movie
poster art myself). Then:
```powershell
copy .env.example .env
notepad .env
```
Add **one** TMDB credential (`TMDB_ACCESS_TOKEN` v4, or `TMDB_API_KEY` v3 — not both) and save.
No other setup needed — this writes straight into the same local SQLite database:
```powershell
python setup_check.py
python scripts\fetch_movies.py --pages 20          # add --details for TMDB keywords too
python scripts\build_features.py
python app.py
```
This adds real movies with real posters alongside (or instead of, after you clear `data/movieflix.db`)
the sample ones, and the in-app notice about placeholder posters disappears automatically.

### Optional: use your own MySQL server instead
Set `DB_ENGINE=mysql` in `.env`, start MySQL and set its password there too, then run the same
three commands above.

## What's new
**Front end (scroll-driven, no libraries):**
- Full-screen hero slideshow (auto-rotating, dots) with parallax backdrop that fades/moves as you scroll
- Scroll progress bar, navbar that turns solid on scroll and hides when scrolling down / returns on scroll up
- Netflix-style horizontal rows (Trending, Top Rated, New Releases, 6 genres) with arrows and snap scrolling
- Reveal-on-scroll animations, hover cards with quick overview + rating, "% match" on recommendations
- Live search suggestions, genre browsing, back-to-top button, mobile friendly, respects `prefers-reduced-motion`
- Movie page with backdrop hero and a "Because you viewed …" row

**Zero-setup demo mode:** `DB_ENGINE=sqlite` (the default) stores everything in a local file and seeds
it from `demo_data.py` on first run — no MySQL, no TMDB key, no `.env` needed at all.

**Bugs fixed:** see `CHANGES.md`.

## Weeks completed
1. **TMDB data collection:** authentication, discovery, JSON, MySQL.
2. **Web crawling:** BeautifulSoup metadata extraction example.
3. **Information retrieval:** cleaning, TF-IDF, cosine similarity, ranked content-based recommendations.
4. **Backend:** Flask, MySQL, search, details, recommendation API, health check.
5. **Frontend/testing:** Netflix-style UI, poster fallback, evaluation and pytest tests.

## Credential fix
The client supports **both** TMDB v4 Read Access Token and TMDB v3 API Key. Put only one in `.env`:

`TMDB_ACCESS_TOKEN=...` (v4 preferred) OR `TMDB_API_KEY=...` (v3 fallback).

Do not add `Bearer` to the value. The previous project failed because it required v4 only; this version accepts either official credential type.


## Test API
```powershell
python tmdb_client.py
```

## Collect data
```powershell
python scripts\fetch_movies.py --pages 20
```
For a larger dataset:
```powershell
python scripts\fetch_movies.py --pages 50
```
Better recommendations (also stores TMDB keywords, slower):
```powershell
python scripts\fetch_movies.py --pages 20 --details
```

## Build recommendation model
```powershell
python scripts\build_features.py
```

## Evaluate
```powershell
python evaluator.py
pytest -q
```


## Poster error fix
Invalid, empty, or missing TMDB `poster_path` values never become `/None`, `/`, or another broken URL. They use `poster-fallback.svg`. Every movie card also has an HTML `onerror` fallback, so an unavailable remote poster is replaced automatically.

## Important
TMDB supplies movie metadata and image URLs. This project does not download or redistribute movie video files.
