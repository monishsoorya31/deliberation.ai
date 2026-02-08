
from django.urls import path
from .views import StartDeliberationView, MessageStreamView, ConversationHistoryView

urlpatterns = [
    path('conversation/start/', StartDeliberationView.as_view(), name='start_deliberation'),
    path('conversation/<str:conversation_id>/stream/', MessageStreamView.as_view(), name='message_stream'),
    path('conversation/<str:conversation_id>/history/', ConversationHistoryView.as_view(), name='conversation_history'),
]
