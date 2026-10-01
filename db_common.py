"""Shared row shape used by both DB backends (mysql, sqlite)."""
import genres as G
import poster_art

COLUMNS = ["id", "title", "original_title", "overview", "release_date", "vote_average",
           "vote_count", "popularity", "poster_path", "poster_url", "backdrop_path",
           "backdrop_url", "genres", "keywords", "language", "adult"]


def clean(row):
    """Make a DB row safe/convenient for templates and JSON."""
    if not row:
        return row
    r = dict(row)
    r["vote_average"] = float(r.get("vote_average") or 0)
    r["popularity"] = float(r.get("popularity") or 0)
    r["vote_count"] = int(r.get("vote_count") or 0)
    r["adult"] = bool(r.get("adult"))
    rd = r.get("release_date")
    r["release_date"] = rd.isoformat() if hasattr(rd, "isoformat") else str(rd or "")
    r["year"] = r["release_date"][:4]
    r["title"] = r.get("title") or r.get("original_title") or "Untitled"

    poster = r.get("poster_url") or ""
    if not poster and r.get("poster_path"):
        pp = r["poster_path"]
        poster = pp if pp.startswith("http") else f"https://image.tmdb.org/t/p/w500{pp}"
        r["poster_url"] = poster

    r["poster"] = poster if poster.startswith(("http://", "https://")) else \
        poster_art.poster_svg(r["title"], r.get("id") or 0, r["year"])

    back = r.get("backdrop_url") or ""
    if not back and r.get("backdrop_path"):
        bp = r["backdrop_path"]
        back = bp if bp.startswith("http") else f"https://image.tmdb.org/t/p/w1280{bp}"
        r["backdrop_url"] = back

    r["backdrop"] = back if back.startswith(("http://", "https://")) else ""
    r["genre_list"] = G.names(r.get("genres"))
    r["overview"] = r.get("overview") or ""
    return r
