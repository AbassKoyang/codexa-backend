from django.urls import path
from .views import AIChatView, AICodeAssistantView

urlpatterns = [
    path('chat/', AIChatView.as_view(), name='ai_chat'),
    path('assistant/', AICodeAssistantView.as_view(), name='ai_assistant'),
]
