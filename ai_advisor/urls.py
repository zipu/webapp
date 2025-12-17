"""
AI Advisor URL Configuration
"""

from django.urls import path
from . import views

app_name = 'ai_advisor'

urlpatterns = [
    # 메인 채팅 페이지
    path('chat/', views.ChatView.as_view(), name='chat'),

    # API 엔드포인트
    path('send_message/', views.send_message, name='send_message'),
    path('new_conversation/', views.new_conversation, name='new_conversation'),
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversation/<int:conversation_id>/', views.get_conversation, name='get_conversation'),

    # 메모리 관리 API
    path('conversation/<int:conversation_id>/memories/', views.get_memories, name='get_memories'),
    path('conversation/<int:conversation_id>/memories/create/', views.create_memory, name='create_memory'),
    path('conversation/<int:conversation_id>/extract_memories/', views.extract_memories, name='extract_memories'),
    path('conversation/<int:conversation_id>/summary_stats/', views.get_summary_stats, name='summary_stats'),
    path('memory/<int:memory_id>/', views.delete_memory, name='delete_memory'),
    path('message/<int:message_id>/save_memory/', views.save_message_as_memory, name='save_message_as_memory'),
]
