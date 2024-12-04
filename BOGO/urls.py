from django.contrib import admin
from django.urls import path, include
from users.views import CustomConfirmEmailView
from dj_rest_auth.registration.views import VerifyEmailView
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('accounts/email-confirm-complete/', TemplateView.as_view(template_name="account/email_confirm_complete.html"), name="email_confirm_complete"),
    path('accounts/', include('allauth.urls')),  # django-allauth URL 포함
    path('api/users/', include('users.urls')),  # users 앱의 API 엔드포인트 포함
    path('api/recipes/', include('recipes.urls')),
]
