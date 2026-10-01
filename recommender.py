"""Content-based recommendations (TF-IDF + cosine similarity)."""
from pathlib import Path
import pickle
import numpy as np
from sklearn.metrics.pairwise import linear_kernel
import config
import db
import genres as G

MODEL = Path(config.BASE_DIR) / "data/processed/tfidf.pkl"
_state = {"mtime": None}


def _load():
    """Load the model once and reload only if the file changes (was: re-read on every request)."""
    if not MODEL.exists():
        return None
    mtime = MODEL.stat().st_mtime
    if _state["mtime"] != mtime:
        with open(MODEL, "rb") as f:
            data = pickle.load(f)
        ids = [int(i) for i in data["movie_ids"]]
        _state.update(mtime=mtime, matrix=data["matrix"].tocsr(), ids=ids,
                      index={m: i for i, m in enumerate(ids)})
    return _state


def _fallback(mid, limit):
    """No model / unknown movie: show popular movies from the same genre."""
    m = db.one(mid)
    gids = G.ids(m.get("genres")) if m else []
    if not gids:
        return []
    out = []
    for x in db.top("popular", limit, genre_id=gids[0], exclude=mid):
        x = dict(x); x["similarity"] = None
        out.append(x)
    return out


def recommend(mid, limit=12):
    mid, limit = int(mid), int(limit)
    s = _load()
    if s and mid in s["index"]:
        i = s["index"][mid]
        scores = linear_kernel(s["matrix"][i], s["matrix"]).ravel()  # TF-IDF rows are L2-normalised
        scores[i] = -1
        n = min(limit * 2, len(scores) - 1)  # ask for extras in case some rows left the DB
        if n > 0:
            top = np.argpartition(-scores, n - 1)[:n]
            top = top[np.argsort(-scores[top])]
            cand = [(s["ids"][j], float(scores[j])) for j in top if scores[j] > 0]
            found = {m["id"]: m for m in db.by_ids([c[0] for c in cand])}
            out = []
            for cid, sc in cand:
                if cid in found:
                    m = dict(found[cid]); m["similarity"] = round(sc, 4)
                    out.append(m)
                if len(out) >= limit:
                    break
            if out:
                return out
    return _fallback(mid, limit)
