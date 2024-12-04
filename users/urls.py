### in users_urls.py ###

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignUpView,
    SignInView,
    PasswordResetView,
    UserDetailView,
    UserAccountUpdate,
    DeleteAccountView,
    LogoutView,
    UserIngreListView,
    UserExceptIngreView,
    UserLevelView,
    BookmarkView,
    HistoryView,
)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('profile/', UserDetailView.as_view(), name='user_detail'),  # 회원정보 조회
    path('profile/update/', UserAccountUpdate.as_view(), name='user_account_update'),  # 회원정보 업데이트
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('ingredients/', UserIngreListView.as_view(), name='user_ingredients'),
    path('except-ingredients/', UserExceptIngreView.as_view(), name='user_except_ingredients'),
    path('level/', UserLevelView.as_view(), name='user_level'),
    path('bookmarks/', BookmarkView.as_view(), name='user_bookmarks'),
    path('history/', HistoryView.as_view(), name='user_history'),
]

