import joblib
import os

# 1. Load model and vectorizer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = joblib.load(os.path.join(BASE_DIR, 'genre_model.pkl'))
vectorizer = joblib.load(os.path.join(BASE_DIR, 'vectorizer.pkl'))

# 2. Input your book title and summary
title = input("Enter the book title: ")
summary = input("Enter the book summary: ")

# 3. Combine title and summary
text = title + ' ' + summary

# 4. Vectorize input
text_vectorized = vectorizer.transform([text])

# 5. Predict genre
predicted_genre = model.predict(text_vectorized)[0]

print(f"\n🎯 Predicted Genre: {predicted_genre}")
