from __future__ import annotations

import os
import pickle
import requests


from collections import Counter
from pathlib import Path
from typing import Any
from datetime import datetime

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "accept": "application/json"
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

def tmdb_get(endpoint, params=None):
    response = requests.get(
        f"{TMDB_BASE_URL}/{endpoint}",
        headers=TMDB_HEADERS,
        params=params,
        timeout=15
    )
    response.raise_for_status()
    return response.json()


def get_tmdb_movies():
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not configured.")

    popular = tmdb_get("movie/popular", {"language": "en-US", "page": 1})

    genres_data = tmdb_get("genre/movie/list", {"language": "en"})
    genres = {
        item["id"]: item["name"]
        for item in genres_data.get("genres", [])
    }

    movies = []

    for item in popular.get("results", [])[:8]:
        movie_id = item["id"]

        review_data = tmdb_get(
            f"movie/{movie_id}/reviews",
            {"language": "en-US", "page": 1}
        )

        reviews = []

        for review in review_data.get("results", []):
            reviews.append({
                "user": review.get("author", "Anonymous"),
                "text": review.get("content", "")
            })

        genre_ids = item.get("genre_ids", [])
        genre = genres.get(genre_ids[0], "Movie") if genre_ids else "Movie"

        movies.append({
            "id": str(movie_id),
            "title": item.get("title", "Untitled"),
            "year": item.get("release_date", "")[:4],
            "genre": genre,
            "description": item.get("overview", ""),
            "poster_path": (
                f"{TMDB_IMAGE_URL}{item['poster_path']}"
                if item.get("poster_path") else None
            ),
            "backdrop_path": (
                f"https://image.tmdb.org/t/p/w1280{item['backdrop_path']}"
                if item.get("backdrop_path") else None
            ),
            "reviews": reviews
        })

    return movies


def predict_emotion(review: str) -> str:
    return str(model.predict(vectorizer.transform([review]))[0]).lower()


def analyze_movie(movie: dict[str, Any]) -> dict[str, Any]:
    scored = [{**review, "emotion": predict_emotion(review["text"])} for review in movie["reviews"]]
    counts = Counter(item["emotion"] for item in scored)
    total = len(scored)
    distribution = {e: round(counts.get(e, 0) * 100 / total) if total else 0 for e in EMOTIONS}
    headline = max(EMOTIONS, key=lambda e: counts.get(e, 0)) if total else "neutral"
    return {**{k: v for k, v in movie.items() if k != "reviews"},
            "reviews": scored, "review_count": total, "distribution": distribution,
            "predicted_emotion": headline, "leading_count": counts.get(headline, 0),
            "leading_percent": distribution.get(headline, 0)}


@app.get("/")
def home():
    return render_template("index.html", emotions=EMOTION_META)


@app.get("/api/movies")
def get_movies():
    try:
        movies = get_tmdb_movies()
        return jsonify([
            analyze_movie(movie) for movie in movies
        ])

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to TMDB.",
            "details": str(error)
        }), 502

    except RuntimeError as error:
        return jsonify({"error": str(error)}), 500


@app.post("/api/analyze")
def analyze_review():
    payload = request.get_json(silent=True) or {}
    review = str(payload.get("review", "")).strip()
    if not review:
        return jsonify({"error": "Please enter a movie review."}), 400
    if len(review) > 5000:
        return jsonify({"error": "Please keep reviews under 5,000 characters."}), 400
    emotion = predict_emotion(review)
    return jsonify({"review": review, "predicted_emotion": emotion,
                    "emotion_label": EMOTION_META.get(emotion, {}).get("label", emotion.title())})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": True,
                    "emotions": list(getattr(model, "classes_", EMOTIONS))})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG") == "1")
