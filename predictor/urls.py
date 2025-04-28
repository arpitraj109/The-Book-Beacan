from django.urls import path, include
from .views import predict_view, signup_view, save_favorite, bookshelf, remove_favorite, get_book_details_ajax, submit_review

urlpatterns = [
    path('', predict_view, name='predict'),
    path('signup/', signup_view, name='signup'),
    path('save_favorite/', save_favorite, name='save_favorite'),
    path('bookshelf/', bookshelf, name='bookshelf'),
    path('remove_favorite/<int:book_id>/', remove_favorite, name='remove_favorite'),
    path('get_book_details/', get_book_details_ajax, name='get_book_details'),
    path('submit_review/', submit_review, name='submit_review'),
    path('accounts/', include('django.contrib.auth.urls')),
]
