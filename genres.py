"""TMDB genre id <-> name helpers."""

GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War",
    37: "Western",
}


def _tokens(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [t.strip() for t in str(value).split(",") if t.strip()]


def ids(value):
    """'28,12' -> [28, 12] (names are ignored)."""
    return [int(t) for t in _tokens(value) if t.isdigit()]


def names(value):
    """'28,12' or 'Action,Adventure' -> ['Action', 'Adventure']."""
    out = []
    for t in _tokens(value):
        name = GENRES.get(int(t)) if t.isdigit() else t
        if name:
            out.append(name)
    return out
