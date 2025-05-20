from django.urls import path
from . import views

urlpatterns = [
    # Welcome Page Flow Control
    path('', views.welcome, name='welcome'),

    # Home Page Flow Control
    path('content/', views.home, name='home'),

    path('developer/<str:username>/', views.developer_profile_view, name='developer_profile'),

    # Explore Page Flow Control
    path('Explore/', views.home, name='explore'),

    # Content Upload Flow Control
    path('upload/', views.upload_code, name='upload_content'),

    # Content Detail View Flow Control
    path('code/<int:code_id>/', views.code_detail, name='code_detail'),

    # User Uploaded Content Flow Control
    path('my_content/', views.my_content, name='my_content'),

    # User Uploaded Content Update Flow Control
    path('update/<int:pk>/', views.update_content, name='update_content'),

    # User Uploaded Content Delete Flow Control
    path('delete/<int:pk>/', views.delete_content, name='delete_content'),

    path('category/<slug:val>', views.CategoryView.as_view(), name='category'),

    path('about/', views.about, name='about'),

    path('contact/', views.contact, name='contact'),

    path('terms/', views.terms, name='terms'),

    path('privacy/', views.privacy, name='privacy'),
    
    # Development Page Flow Control
    path('Development-phase/rough_page/', views.rough, name='rough'),
]
