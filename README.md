# ReelFeel — Movie Emotion Studio

A dark, cinematic Flask dashboard for exploring emotions expressed in movie reviews. It uses a supplied TF-IDF vectorizer and Linear SVC model to classify reviews into **joy, sadness, anger, fear, surprise,** or **neutral**.

## Features

- Film library with title search and selectable movie views
- Emotion breakdown and leading-emotion summary calculated from model predictions
- Individual review cards with their predicted emotion
- Quick analysis modal for any new review
- JSON endpoints for the frontend and future integrations
- Responsive layout for desktop and mobile
- Cinematic first-visit screen when no movie is selected

## Required model files

Place these two trusted model artifacts beside `app.py` before starting the server:

- `best_emotion_detection_model.pkl`
- `tfidf_vectorizer.pkl`

**Important:** the binary model artifacts are not part of this initial source upload. The application needs both files at startup. Do not load pickle files from untrusted sources.

## Run locally

Python 3.10–3.12 is recommended. The model artifacts were serialized with scikit-learn 1.6.1.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

## API endpoints

- `GET /api/movies` — starter movie list, review-level predictions and emotion distribution.
- `POST /api/analyze` — classify a review. Example body: `{"review":"The story was moving and the ending made me smile."}`
- `GET /health` — model status and available model classes.

The starter movie/review content is demonstration content; replace it with your real dataset when ready. Percentages represent the share of reviews assigned to each class, not probability/confidence scores.

## Security

Never commit API keys, passwords, private datasets, or `.env` files. Keep future API credentials in environment variables.
