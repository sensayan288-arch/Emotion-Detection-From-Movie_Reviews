# ReelFeel — Movie Emotion Studio

ReelFeel is a cinematic Flask dashboard that explores emotions expressed in movie reviews. It uses a trained TF-IDF vectorizer and emotion-classification model to classify reviews into **joy, sadness, anger, fear, surprise,** or **neutral**.

## Features

- Fetches popular movies, genres, posters, and backdrops from TMDB
- Fetches available English user reviews from each movie's TMDB reviews endpoint
- Scores each fetched review with the supplied emotion model
- Displays an emotion distribution and individual review predictions
- Includes quick analysis for a review pasted by the user
- Responsive dark cinematic interface with a first-visit landing screen

## Requirements

- Python 3.10–3.12 recommended
- A TMDB account and API Read Access Token
- Both trusted model files listed below

## Model files

Place these files beside `app.py`:

- `best_emotion_detection_model.pkl`
- `tfidf_vectorizer.pkl`

The application loads these pickle files at startup. Only use model files from a trusted source. The serialized model was prepared with scikit-learn 1.6.1.

## Run locally

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set your TMDB **API Read Access Token** as an environment variable. Do not paste the token into source code or commit it to GitHub.

Windows PowerShell:

```powershell
$env:TMDB_API_KEY="YOUR_TMDB_READ_ACCESS_TOKEN"
python app.py
```

macOS/Linux:

```bash
export TMDB_API_KEY="YOUR_TMDB_READ_ACCESS_TOKEN"
python app.py
```

Open <http://127.0.0.1:5000>.

## Deploy on Render

1. Create a Render Web Service connected to this GitHub repository.
2. Use `pip install -r requirements.txt` as the build command.
3. Use `gunicorn app:app` as the start command.
4. In the Render service's **Environment** settings, add `TMDB_API_KEY` with your TMDB API Read Access Token.
5. Ensure both model files are present in the deployed repository beside `app.py`, then deploy.

Never commit the TMDB token or a local `.env` file.

## API endpoints

- `GET /` — ReelFeel dashboard.
- `GET /api/movies` — popular TMDB movies with available reviews and model predictions.
- `POST /api/analyze` — classify a review. Example JSON body: `{"review":"The story was moving and the ending made me smile."}`.
- `GET /health` — model status and whether the TMDB token is configured.

## Notes

TMDB may return no reviews for some movies. Such movies remain visible, but their emotion distribution is empty. The displayed percentages represent the share of fetched reviews assigned to each emotion, not probability or model confidence scores.

This product uses the TMDB API but is not endorsed or certified by TMDB.
