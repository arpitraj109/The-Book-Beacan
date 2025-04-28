import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib
import os

# 1. Load Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, 'books.csv')

df = pd.read_csv(data_path)

# 2. Check columns
print(df.columns)

# 3. Combine title and summary into one text
df['text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('')

# 4. Features and Labels
X = df['text']
y = df['genre']   # <-- lowercase!

# 5. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. Train Model
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000)),
    ('clf', LogisticRegression(max_iter=1000))
])

pipeline.fit(X_train, y_train)

# 7. Save Model and Vectorizer
joblib.dump(pipeline, os.path.join(BASE_DIR, 'genre_predictor.joblib'))

print("✅ Model trained and saved successfully!")
