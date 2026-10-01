from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re
import mysql.connector
import config, db, recommender
import genres as G

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

FEATURED_GENRES = [(28, "Action"), (35, "Comedy"), (878, "Sci-Fi"), (27, "Horror"), (18, "Drama"), (16, "Animation")]


@app.context_processor
def inject_globals():
    try:
        demo = not db.has_real_posters()
    except Exception:
        demo = False
    uid = session.get("user_id")
    current_user = None
    if uid:
        try:
            current_user = db.get_user_by_id(uid)
        except Exception:
            current_user = None
    return {
        "ALL_GENRES": sorted(G.GENRES.items(), key=lambda kv: kv[1]),
        "DEMO_POSTERS": demo,
        "current_user": current_user,
        "is_auth_page": request.endpoint in ("login", "register")
    }


@app.get("/")
def home():
    hero = db.top("popular", 5)  # backdrop is optional; slides without one get a styled gradient
    all_m = db.all_movies()
    indian = [m for m in all_m if m.get("language") in ("hi", "te", "ta", "kn", "ml", "bn")]
    rows = [("Trending Now", db.top("popular", 20))]
    if indian:
        rows.append(("Indian Blockbusters", indian[:20]))
    rows += [("Top Rated", db.top("rated", 20)),
             ("New Releases", db.top("latest", 20))]
    rows += [(name, db.top("popular", 20, genre_id=gid)) for gid, name in FEATURED_GENRES]
    rows = [(title, movies) for title, movies in rows if movies]
    return render_template("index.html", hero=hero, rows=rows)


@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    return render_template("search.html", movies=db.search(q, 60), query=q, heading=f"Results for “{q}”" if q else "All movies")


@app.get("/genre/<int:gid>")
def genre(gid):
    if gid not in G.GENRES:
        abort(404)
    return render_template("search.html", movies=db.top("popular", 60, genre_id=gid), query="",
                           heading=G.GENRES[gid], active_genre=gid)


@app.get("/movie/<int:mid>")
def movie(mid):
    m = db.one(mid)
    if not m:
        abort(404)
    return render_template("movie.html", movie=m, recommendations=recommender.recommend(mid, 16))


@app.get("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify([{"id": m["id"], "title": m["title"], "year": m["year"], "poster": m["poster"],
                     "rating": round(m["vote_average"], 1)} for m in db.search(q, 6)])


@app.get("/api/recommendations/<int:mid>")
def rec(mid):
    return jsonify(recommender.recommend(mid, 20))


@app.get("/api/poster/<int:mid>")
def api_poster(mid):
    m = db.one(mid)
    if not m:
        abort(404)
    return jsonify({
        "id": m["id"],
        "title": m["title"],
        "poster": m["poster"],
        "poster_url": m.get("poster_url") or m["poster"],
        "backdrop": m.get("backdrop") or "",
        "backdrop_url": m.get("backdrop_url") or m.get("backdrop") or ""
    })


@app.get("/health")
def health():
    try:
        return jsonify(status="ok", movies=db.count())
    except Exception as e:  # noqa: BLE001
        return jsonify(status="error", message=str(e)), 500


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        form_data = {"username": username, "email": email}

        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if len(username) < 3 or len(username) > 30:
            flash("Username must be between 3 and 30 characters.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            flash("Username can only contain letters, numbers, and underscores.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            flash("Please enter a valid email address.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if db.get_user_by_username(username):
            flash("Username is already taken. Please choose another.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        if db.get_user_by_email(email):
            flash("Email is already registered. Please sign in instead.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        pwd_hash = generate_password_hash(password)
        user = db.create_user(username, email, pwd_hash)
        if not user:
            flash("Could not create account. Please try again.", "error")
            return render_template("auth.html", mode="register", form_data=form_data)

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Account created successfully! Welcome to MovieFlix, {user['username']}.", "success")
        return redirect(url_for("home"))

    return render_template("auth.html", mode="register", form_data={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        identifier = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        form_data = {"email": identifier}

        if not identifier or not password:
            flash("Please provide both email/username and password.", "error")
            return render_template("auth.html", mode="login", form_data=form_data)

        user = None
        if "@" in identifier:
            user = db.get_user_by_email(identifier) or db.get_user_by_username(identifier)
        else:
            user = db.get_user_by_username(identifier) or db.get_user_by_email(identifier)

        if not user or not check_password_hash(user.get("password_hash", ""), password):
            flash("Invalid email/username or password.", "error")
            return render_template("auth.html", mode="login", form_data=form_data)

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(url_for("home"))

    return render_template("auth.html", mode="login", form_data={})


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, title="Page not found",
                           message="That movie or page doesn't exist."), 404


@app.errorhandler(mysql.connector.Error)
def db_error(e):
    return render_template("error.html", code=503, title="Database not ready",
                           message="Start MySQL, check .env, then run scripts/fetch_movies.py.",
                           detail=str(e)), 503


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG)
