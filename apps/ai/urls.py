from django.urls import path
from .views import AIChatView, AICodeAssistantView, ChatHistoryView

urlpatterns = [
    path('autocomplete/', AIChatView.as_view(), name='ai_autocomplete'),
    path('assistant/', AICodeAssistantView.as_view(), name='ai_assistant'),
    path('history/<slug:project_slug>/', ChatHistoryView.as_view(), name='chat_history'),
]
