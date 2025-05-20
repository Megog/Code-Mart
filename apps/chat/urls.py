# Digital_Content_Marketplace/apps/chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('thread/<int:thread_id>/', views.chat_view, name='chat_view'),
    path('thread/<int:thread_id>/preview/', views.preview_code, name='preview_code'),
    path('thread/<int:thread_id>/download/', views.download_code, name='download_code'),
    path('admin/chat/', views.admin_chat_view, name='admin_chat_view'),  # Thread list
    path('admin/chat/<int:thread_id>/', views.admin_chat_view, name='admin_chat_view'),
    path('initiate/<int:code_id>/', views.initiate_chat, name='initiate_chat'),
    path('notifications/', views.notifications, name='notifications'),
    path('active_chats/', views.active_chats, name='active_chats'),
]