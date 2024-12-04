### in recipes/urls.py ###

from django.urls import path
from .views import (
    AllRecipesView, 
    FilteredRecipesView,
)

urlpatterns = [
    path('all-recipes/', AllRecipesView.as_view(), name='all_recipes'),
    path('filtered-recipes/', FilteredRecipesView.as_view(), name='filtered_recipes'),
]

