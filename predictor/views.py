from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import BookForm, SignUpForm, ReviewForm
from .ml_model.predict_util import predict_genre
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import FavoriteBook, RecentSearch, Review
import requests
import urllib.parse
from django.db import models
import random

# Genre to icon mapping
GENRE_ICONS = {
    "Fantasy": "bi-magic",
    "Mystery": "bi-search",
    "Romance": "bi-heart-fill",
    "Science Fiction": "bi-rocket-takeoff",
}

# Genre to description mapping
GENRE_DESCRIPTIONS = {
    "Fantasy": "Fantasy books feature magical worlds, mythical creatures, and epic adventures.",
    "Mystery": "Mystery books revolve around solving a crime, uncovering secrets, or unraveling puzzles.",
    "Romance": "Romance books focus on love stories, relationships, and emotional connections.",
    "Science Fiction": "Science Fiction explores futuristic technology, space travel, and imaginative science-based concepts.",
}

# Static book recommendations by genre
GENRE_RECOMMENDATIONS = {
    "Fantasy": [
        {"title": "Harry Potter and the Sorcerer's Stone", "author": "J.K. Rowling"},
        {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
        {"title": "The Name of the Wind", "author": "Patrick Rothfuss"},
    ],
    "Mystery": [
        {"title": "The Hound of the Baskervilles", "author": "Arthur Conan Doyle"},
        {"title": "Gone Girl", "author": "Gillian Flynn"},
        {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson"},
    ],
    "Romance": [
        {"title": "Pride and Prejudice", "author": "Jane Austen"},
        {"title": "The Notebook", "author": "Nicholas Sparks"},
        {"title": "Me Before You", "author": "Jojo Moyes"},
    ],
    "Science Fiction": [
        {"title": "Dune", "author": "Frank Herbert"},
        {"title": "Ender's Game", "author": "Orson Scott Card"},
        {"title": "Neuromancer", "author": "William Gibson"},
    ],
}

# Placeholder cover image
PLACEHOLDER_COVER = "https://via.placeholder.com/200x300?text=No+Cover"

# Utility to generate buy/view links for a book
def get_buy_links(title, author, work_key=None):
    query = urllib.parse.quote_plus(f'{title} {author}')
    links = {
        'amazon': f'https://www.amazon.com/s?k={query}',
        'bn': f'https://www.barnesandnoble.com/s/{query}',
        'openlibrary': f'https://openlibrary.org{work_key}' if work_key else f'https://openlibrary.org/search?q={query}',
    }
    return links

def get_quotes(title, author):
    quotes = []
    
    # Try Open Library first
    try:
        # Search for the book
        search_url = f"https://openlibrary.org/search.json?title={urllib.parse.quote(title)}&author={urllib.parse.quote(author)}"
        search_resp = requests.get(search_url, timeout=3)
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            if search_data.get('docs'):
                work_key = search_data['docs'][0].get('key')
                if work_key:
                    work_url = f"https://openlibrary.org{work_key}.json"
                    work_resp = requests.get(work_url, timeout=3)
                    if work_resp.status_code == 200:
                        work_data = work_resp.json()
                        if 'quotes' in work_data:
                            quotes.extend(work_data['quotes'])
                        if 'excerpts' in work_data:
                            quotes.extend([excerpt.get('text', '') for excerpt in work_data['excerpts'] if excerpt.get('text')])
    except Exception:
        pass
    
    # If no quotes found, try Goodreads API (using their public API)
    if not quotes:
        try:
            goodreads_url = f"https://www.goodreads.com/quotes/search?q={urllib.parse.quote(f'{title} {author}')}"
            goodreads_resp = requests.get(goodreads_url, timeout=3)
            if goodreads_resp.status_code == 200:
                # Parse the response to extract quotes
                # Note: This is a simplified example. You might need to adjust the parsing based on the actual response
                quotes.extend([quote for quote in goodreads_resp.text.split('class="quoteText"') if quote.strip()])
        except Exception:
            pass
    
    # If still no quotes, add some generic book quotes
    if not quotes:
        generic_quotes = [
            "A reader lives a thousand lives before he dies. The man who never reads lives only one.",
            "The more that you read, the more things you will know. The more that you learn, the more places you'll go.",
            "Books are a uniquely portable magic.",
            "There is no friend as loyal as a book.",
            "A book is a dream that you hold in your hand.",
            "Reading is to the mind what exercise is to the body.",
            "Books are the quietest and most constant of friends.",
            "The world belongs to those who read.",
            "A book is a device to ignite the imagination.",
            "Reading is a conversation. All books talk. But a good book listens as well."
        ]
        quotes.extend(random.sample(generic_quotes, 3))
    
    return quotes

# Fetch book details from Open Library (improved for better description and author matching)
def get_book_details(title):
    url = f"https://openlibrary.org/search.json?title={title}"
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get('docs', [])
            preferred_authors = [
                'jane austen', 'j.k. rowling', 'jk rowling', 'tolkien', 'frank herbert', 'arthur conan doyle', 'gillian flynn', 'nicholas sparks', 'jojo moyes', 'william gibson', 'orson scott card', 'patrick rothfuss', 'stieg larsson'
            ]
            doc = None
            for d in docs[:10]:
                author_list = d.get('author_name', [])
                author_str = ' '.join(author_list).lower() if author_list else ''
                for pa in preferred_authors:
                    if pa in author_str:
                        doc = d
                        break
                if doc:
                    break
            if not doc and docs:
                doc = docs[0]
            if doc:
                author_list = doc.get('author_name', [])
                author = author_list[0].strip() if author_list else 'Not found'
                author_key_list = doc.get('author_key', [])
                author_key = author_key_list[0] if author_key_list else None
                cover_url = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg" if 'cover_i' in doc else PLACEHOLDER_COVER
                description = None
                work_key = doc.get('key')
                
                if work_key:
                    work_url = f"https://openlibrary.org{work_key}.json"
                    try:
                        work_resp = requests.get(work_url, timeout=3)
                        if work_resp.status_code == 200:
                            work_data = work_resp.json()
                            desc = work_data.get('description')
                            if isinstance(desc, dict):
                                description = desc.get('value')
                            elif isinstance(desc, str):
                                description = desc
                    except Exception:
                        pass
                
                if not description:
                    description = doc.get('first_sentence') or doc.get('subtitle') or doc.get('subject')
                    if isinstance(description, list):
                        description = description[0]
                if not description:
                    description = 'Not found'
                
                # Get quotes from multiple sources
                quotes = get_quotes(title, author)
                
                buy_links = get_buy_links(title, author, work_key)
                return author, description, cover_url, author_key, buy_links, quotes
    except Exception:
        pass
    return 'Not found', 'Not found', PLACEHOLDER_COVER, None, get_buy_links(title, '', None), []

# Fetch other books by the same author from Open Library using author_key if available
def get_author_books(author, exclude_title, author_key=None):
    books = []
    if author_key:
        url = f"https://openlibrary.org/search.json?author={author_key}"
    elif author and author != 'Not found':
        url = f"https://openlibrary.org/search.json?author={requests.utils.quote(author)}"
    else:
        return []
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            for doc in data.get('docs', []):
                title = doc.get('title')
                if title and title.lower() != exclude_title.lower():
                    book_author = ', '.join(doc.get('author_name', [])) if doc.get('author_name') else author
                    work_key = doc.get('key')
                    books.append({
                        'title': title,
                        'author': book_author,
                        'buy_links': get_buy_links(title, book_author, work_key)
                    })
                if len(books) >= 5:
                    break
            return books
    except Exception:
        pass
    return []

def predict_view(request):
    result = None
    genre_icon = "bi-book"
    genre_description = ""
    cover_url = PLACEHOLDER_COVER
    recommendations = []
    author_books = []
    book_author = ''
    book_description = ''
    author_key = None
    main_buy_links = {}
    recent_searches = []
    quotes = []
    
    if request.user.is_authenticated:
        recent_searches = RecentSearch.objects.filter(user=request.user).order_by('-searched_at')[:5]
    
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            # Track search if user is authenticated
            if request.user.is_authenticated:
                RecentSearch.objects.create(user=request.user, title=title)
            # Fetch book details from Open Library
            book_author, book_description, cover_url, author_key, main_buy_links, quotes = get_book_details(title)
            # Fetch other books by the same author (prefer author_key)
            author_books = get_author_books(book_author, title, author_key)
            genre, confidence = predict_genre(title, book_description)
            result = {
                'genre': genre,
                'confidence': f"{confidence*100:.1f}%"
            }
            genre_icon = GENRE_ICONS.get(genre, "bi-book")
            genre_description = GENRE_DESCRIPTIONS.get(genre, "Enjoy exploring this genre!")
            # Add buy links to genre recommendations
            recs = GENRE_RECOMMENDATIONS.get(genre, [])
            recommendations = []
            for rec in recs:
                rec_links = get_buy_links(rec['title'], rec['author'])
                recommendations.append({**rec, 'buy_links': rec_links})
    else:
        form = BookForm()
    return render(request, 'predictor/predict.html', {
        'form': form,
        'result': result,
        'genre_icon': genre_icon,
        'genre_description': genre_description,
        'cover_url': cover_url,
        'recommendations': recommendations,
        'book_author': book_author,
        'book_description': book_description,
        'author_books': author_books,
        'main_buy_links': main_buy_links,
        'recent_searches': recent_searches,
        'quotes': quotes,
    })

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after signup
            return redirect('predict')  # Redirect to your main page
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def save_favorite(request):
    if request.method == 'POST':
        title = request.POST.get('fav_title')
        author = request.POST.get('fav_author')
        cover_url = request.POST.get('fav_cover_url')
        openlibrary_url = request.POST.get('fav_openlibrary_url')
        if title and author:
            FavoriteBook.objects.get_or_create(
                user=request.user,
                title=title,
                author=author,
                cover_url=cover_url or '',
                openlibrary_url=openlibrary_url or ''
            )
    return redirect('bookshelf')

@login_required
def bookshelf(request):
    books = FavoriteBook.objects.filter(user=request.user).order_by('-added_at')
    return render(request, 'predictor/bookshelf.html', {'books': books})

@login_required
def remove_favorite(request, book_id):
    book = get_object_or_404(FavoriteBook, id=book_id, user=request.user)
    book.delete()
    return redirect('bookshelf')

def get_book_details_ajax(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        title = request.GET.get('title', '')
        if title:
            author, description, cover_url, author_key, buy_links, quotes = get_book_details(title)
            
            # Get reviews and average rating
            reviews = Review.objects.filter(title=title, author=author)
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            review_count = reviews.count()
            
            # Get user's review if exists
            user_review = None
            if request.user.is_authenticated:
                user_review = reviews.filter(user=request.user).first()
            
            return JsonResponse({
                'title': title,
                'author': author,
                'description': description,
                'cover_url': cover_url,
                'buy_links': buy_links,
                'avg_rating': round(avg_rating, 1) if avg_rating else None,
                'review_count': review_count,
                'user_review': {
                    'rating': user_review.rating if user_review else None,
                    'review_text': user_review.review_text if user_review else None
                } if user_review else None,
                'quotes': quotes
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def submit_review(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        title = request.POST.get('title')
        author = request.POST.get('author')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        
        if title and author and rating:
            review, created = Review.objects.update_or_create(
                user=request.user,
                title=title,
                author=author,
                defaults={
                    'rating': rating,
                    'review_text': review_text
                }
            )
            return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)
