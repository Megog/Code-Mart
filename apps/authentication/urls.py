from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView
from . import views
from apps.content.views import upload_code

urlpatterns = [    
    # Registration Flow:
    path('signup/', signup, name='signup'),

    # Login Flow:
    path("login/", CustomLoginView.as_view(), name="login"),

    # Logout Flow:
    path("logout/", LogoutView.as_view(), name="logout"),

    # CustomerDashboard Flow:
    path("customer/dashboard/", customer_dashboard, name="customer_dashboard"),

    # DeveloperDashboard Flow:
    path("developer/dashboard/", developer_dashboard, name="developer_dashboard"),

    # Profile Flow:
    path('profile/', profile, name='profile'),

    # Profile Update Flow:
    path('update-profile/', update_profile, name='update_profile'),

]
