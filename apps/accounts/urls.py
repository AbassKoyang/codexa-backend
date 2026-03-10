from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import CustomTokenObtainPairView

urlpatterns = [
    path('auth/google_login/', views.google_login, name='google-login'),

    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', views.CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/me/', views.MeView.as_view(), name='me'),
]