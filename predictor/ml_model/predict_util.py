import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'genre_predictor.joblib')
model = joblib.load(MODEL_PATH)

def predict_genre(title, description):
    text = f"{title} {description}"
    proba = model.predict_proba([text])[0]
    genre = model.classes_[proba.argmax()]
    confidence = proba.max()
    return genre, confidence
