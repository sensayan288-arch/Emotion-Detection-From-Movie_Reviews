from __future__ import annotations

import os
import pickle
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Set this locally or in Render's Environment settings.
# Use TMDB's API Read Access Token (Bearer token), not the v3 API key.
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p"
MOVIE_CACHE_SECONDS = 600
_movie_cache: dict[str, Any] = {"expires_at": 0.0, "movies": []}

TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "accept": "application/json",
}

# Only load model artifacts that you trust.
with (BASE_DIR / "best_emotion_detection_model.pkl").open("rb") as file:
    model = pickle.load(file)
with (BASE_DIR / "tfidf_vectorizer.pkl").open("rb") as file:
    vectorizer = pickle.load(file)

EMOTIONS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]
EMOTION_META = {
    "joy": {"label": "Joy", "color": "#e8b65d", "icon": "✦"},
    "sadness": {"label": "Sadness", "color": "#83a9e8", "icon": "◒"},
    "anger": {"label": "Anger", "color": "#e47c69", "icon": "⌁"},
    "fear": {"label": "Fear", "color": "#ad91dc", "icon": "◈"},
    "surprise": {"label": "Surprise", "color": "#64c5b2", "icon": "✧"},
    "neutral": {"label": "Neutral", "color": "#9aa0ad", "icon": "—"},
}


def tmdb_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing. Add your TMDB API Read Access Token "
            "to your environment variables."
        )

    response = requests.get(
        f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}",
        headers=TMDB_HEADERS,
        params=params or {},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def get_tmdb_movies() -> list[dict[str, Any]]:
    # Cache TMDB results to avoid repeating API calls on every page refresh.
    now = time.monotonic()
    if now < _movie_cache["expires_at"]:
        return _movie_cache["movies"]

    popular = tmdb_get("movie/popular", {"language": "en-US", "page": 1})
    genres_data = tmdb_get("genre/movie/list", {"language": "en"})
    genres = {
        item["id"]: item["name"]
        for item in genres_data.get("genres", [])
    }

    movies = []
    for item in popular.get("results", [])[:8]:
        movie_id = item["id"]

        # A review endpoint can occasionally fail for an individual title.
        # Keep the movie in the library even if its reviews cannot be fetched.
        try:
            review_data = tmdb_get(
                f"movie/{movie_id}/reviews",
                {"language": "en-US", "page": 1},
            )
            reviews = [
                {
                    "user": review.get("author") or "Anonymous",
                    "text": review.get("content", "").strip(),
                }
                for review in review_data.get("results", [])
                if review.get("content", "").strip()
            ]
        except requests.RequestException:
            reviews = []

        genre_ids = item.get("genre_ids", [])
        genre = genres.get(genre_ids[0], "Movie") if genre_ids else "Movie"
        release_date = item.get("release_date") or ""

        movies.append({
            "id": str(movie_id),
            "title": item.get("title") or "Untitled",
            "year": release_date[:4] or "—",
            "genre": genre,
            "description": item.get("overview") or "No synopsis is available yet.",
            "poster_path": (
                f"{TMDB_IMAGE_URL}/w500{item['poster_path']}"
                if item.get("poster_path") else None
            ),
            "backdrop_path": (
                f"{TMDB_IMAGE_URL}/w1280{item['backdrop_path']}"
                if item.get("backdrop_path") else None
            ),
            "rating": item.get("vote_average"),
            "reviews": reviews,
        })

    _movie_cache["movies"] = movies
    _movie_cache["expires_at"] = time.monotonic() + MOVIE_CACHE_SECONDS
    return movies


def predict_emotion(review: str) -> str:
    return str(model.predict(vectorizer.transform([review]))[0]).lower()


def analyze_movie(movie: dict[str, Any]) -> dict[str, Any]:
    scored = [
        {**review, "emotion": predict_emotion(review["text"])}
        for review in movie["reviews"]
        if review.get("text", "").strip()
    ]
    counts = Counter(item["emotion"] for item in scored)
    total = len(scored)
    distribution = {
        emotion: round(counts.get(emotion, 0) * 100 / total) if total else 0
        for emotion in EMOTIONS
    }
    headline = max(EMOTIONS, key=lambda emotion: counts.get(emotion, 0))
    return {
        **{key: value for key, value in movie.items() if key != "reviews"},
        "reviews": scored,
        "review_count": total,
        "distribution": distribution,
        "predicted_emotion": headline,
        "leading_count": counts.get(headline, 0),
        "leading_percent": distribution[headline],
    }


@app.get("/")
def home():
    return render_template("index.html", emotions=EMOTION_META)


@app.get("/api/movies")
def get_movies():
    try:
        movies = get_tmdb_movies()
        return jsonify([analyze_movie(movie) for movie in movies])
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 500
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else 502
        if status in (401, 403):
            message = "TMDB rejected the request. Check your API Read Access Token."
        elif status == 429:
            message = "TMDB rate limit reached. Please try again shortly."
        else:
            message = "TMDB could not complete the request."
        return jsonify({"error": message}), 502
    except requests.RequestException as error:
        app.logger.exception("TMDB request failed")
        return jsonify({
            "error": "Could not connect to TMDB. Please try again.",
            "details": str(error),
        }), 502


@app.post("/api/analyze")
def analyze_review():
    payload = request.get_json(silent=True) or {}
    review = str(payload.get("review", "")).strip()
    if not review:
        return jsonify({"error": "Please enter a movie review."}), 400
    if len(review) > 5000:
        return jsonify({"error": "Please keep reviews under 5,000 characters."}), 400

    emotion = predict_emotion(review)
    return jsonify({
        "review": review,
        "predicted_emotion": emotion,
        "emotion_label": EMOTION_META.get(emotion, {}).get("label", emotion.title()),
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": True,
        "tmdb_configured": bool(TMDB_API_KEY),
        "emotions": list(getattr(model, "classes_", EMOTIONS)),
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
