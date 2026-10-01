"""Quick sanity check: do recommended movies share genres with the query movie?"""
import db, recommender
import genres as G


def jaccard(a, b):
    a, b = set(G.ids(a)), set(G.ids(b))
    return len(a & b) / len(a | b) if a | b else 0.0


def main(sample=30, k=10):
    movies = db.all_movies()
    print("Movies:", len(movies))
    if not movies:
        return
    first = movies[0]
    print("Sample:", first["title"])
    for x in recommender.recommend(first["id"], k):
        print("-", x["title"], x.get("similarity"))
    scores = []
    for m in movies[:sample]:
        recs = recommender.recommend(m["id"], k)
        if recs:
            scores.append(sum(jaccard(m["genres"], r["genres"]) for r in recs) / len(recs))
    if scores:
        print(f"Mean genre overlap (Jaccard) over {len(scores)} movies: {sum(scores)/len(scores):.3f}")


if __name__ == "__main__":
    main()
