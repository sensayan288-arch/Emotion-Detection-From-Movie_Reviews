from __future__ import annotations

import os
import pickle
from collections import Counter
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

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

# Demo records: replace these with your own movie/review dataset.
MOVIES: list[dict[str, Any]] = [
    {"id": "salt-harbour", "title": "The Salt Harbour", "year": 2023, "genre": "Drama",
     "description": "A widowed ferry pilot takes one last crossing through a storm.",
     "reviews": [
         {"user": "harlow", "text": "I cried through the entire last act. The loneliness of the pilot after losing his wife is handled so gently. A heartbreaking, sorrowful film."},
         {"user": "mina_k", "text": "The quiet scenes were beautiful and the ending gave me a little hope. I loved every minute of it."},
         {"user": "framebyframe", "text": "The storm sequence made me nervous. I was afraid something terrible would happen to the crew."},
         {"user": "noah.r", "text": "The captain's choices made me furious. The story was frustrating, even though the acting was excellent."},
         {"user": "cinemacat", "text": "A lovely surprise. I did not expect the final reveal and it made the whole story feel different."}]},
    {"id": "nine-floors", "title": "Nine Floors Down", "year": 2022, "genre": "Thriller",
     "description": "A night-shift engineer discovers that one elevator has no recorded destination.",
     "reviews": [
         {"user": "reel_rohan", "text": "Every floor was more terrifying than the last. I was on the edge of my seat."},
         {"user": "sanafilm", "text": "The cast brought so much energy. I had a great time watching this clever thriller."},
         {"user": "milesaway", "text": "The ending left me confused and disappointed. The characters deserved a better conclusion."},
         {"user": "pixelpete", "text": "Some scenes were genuinely shocking, and the sound design was fantastic."}]},
    {"id": "paper-lanterns", "title": "Paper Lanterns", "year": 2024, "genre": "Romance",
     "description": "Two childhood friends reconnect during a festival in their hometown.",
     "reviews": [
         {"user": "lena_w", "text": "This film filled me with warmth. Their reunion was so joyful and sweet."},
         {"user": "thelastrow", "text": "I felt sad for both characters. The story reminded me of people I have lost."},
         {"user": "arjunfilm", "text": "A beautiful, gentle surprise with wonderful performances."},
         {"user": "moviemoody", "text": "The misunderstanding made me angry because it could have been solved with one conversation."}]},
    {"id": "fair-account", "title": "A Fair Account", "year": 2021, "genre": "Mystery",
     "description": "An auditor follows a paper trail that leads back to her own family.",
     "reviews": [
         {"user": "drew_reviews", "text": "A clever mystery that kept me guessing. I was delighted by the final twist."},
         {"user": "quietcritic", "text": "The family secrets were disturbing and the atmosphere made me uneasy."},
         {"user": "filmgrain", "text": "I loved the lead performance. It was a satisfying and exciting watch."},
         {"user": "rhea_s", "text": "The corruption made my blood boil. I have never disliked a villain this much."}]},
]


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
    return jsonify([analyze_movie(movie) for movie in MOVIES])


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
