from django.urls import path
from .views import AIChatView

urlpatterns = [
    path('', AIChatView.as_view(), name='ai_chat'),
]
