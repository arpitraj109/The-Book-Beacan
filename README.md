# Book Genre Predictor

A Django web application that predicts the genre of books based on their titles and descriptions.

## Features

- Book genre prediction using machine learning
- User authentication and registration
- Book recommendations by genre
- Favorite books management
- Book reviews and ratings
- Integration with Open Library API for book details

## Installation

1. Clone the repository:
```bash
git clone https://github.com/arpitraj109/The-Book-Beacan.git
cd book-genre-predictor
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

## Usage

1. Access the application at `http://127.0.0.1:8000/`
2. Create an account or log in
3. Enter a book title to get genre predictions and recommendations
4. Save favorite books and write reviews

## Technologies Used

- Django
- Python
- Machine Learning
- Bootstrap
- Open Library API

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
