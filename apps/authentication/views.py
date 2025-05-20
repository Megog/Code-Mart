from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import User, CustomerProfile, DeveloperProfile
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from functools import wraps
from django.contrib import messages

def signup(request):
    if request.user.is_authenticated:
        return redirect('welcome')
    
    form = SignUpForm()
    
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            login(request, user)

            if user.role == 'developer':
                return redirect('developer_dashboard')
            else:
                return redirect('customer_dashboard')
        else:
            print("Form is not valid")
            print("Errors:", form.errors)

    return render(request, 'sign_up.html', {'form': form})


class CustomLoginView(LoginView):
    
    form_class = CustomLoginForm

    template_name = "login.html"
    authentication_form = CustomLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == 'customer':
                return redirect('customer_dashboard')
            elif request.user.role == 'developer':
                return redirect('developer_dashboard')
            else:
                return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'customer':
                return reverse_lazy("customer_dashboard")
            elif user.role == 'developer':
                return reverse_lazy("developer_dashboard")
        return reverse_lazy("home")

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                # Redirect users to their respective dashboards
                return redirect('customer_dashboard' if request.user.role == 'customer' else 'developer_dashboard')
            return redirect('login')  # Redirect to login if not authenticated
        return wrapper
    return decorator

@role_required(allowed_roles=['customer'])
def customer_dashboard(request):
    return render(request, "dashboard.html", {"dashboard_url": "customer_dashboard", "user_role": "customer"})

@role_required(allowed_roles=['developer'])
def developer_dashboard(request):
    return render(request, "dashboard.html", {"dashboard_url": "developer_dashboard", "user_role": "developer"})

@login_required(login_url='login')
def profile(request):
    user = request.user

    # Fetch the correct profile based on the role
    if user.role == 'customer':
        profile, created = CustomerProfile.objects.get_or_create(user=user)
    else:
        profile, created = DeveloperProfile.objects.get_or_create(user=user)


    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def update_profile(request):
    user = request.user

    # Select the correct form based on role
    if user.role == 'customer':
        ProfileForm = CustomerProfileUpdateForm
        profile, created = CustomerProfile.objects.get_or_create(user=user)
    else:
        ProfileForm = DeveloperProfileUpdateForm
        profile, created = DeveloperProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            
            if request.POST.get("clear_profile_picture") == "true":
                user.profile_picture.delete(save=False)  # Remove old file
                user.profile_picture = "profile_pics/user_default.png"

            user_form.save()
            profile_form.save()
            return redirect('profile')  # Redirect to profile page after update

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'update_profile.html', context)

def my_view(request):
    messages.success(request, "Successfully submitted!")
    messages.info(request, "Here's some info.")
    messages.warning(request, "Careful, something might be off.")
    messages.error(request, "Oops! Something went wrong.")
    return redirect('home')  # or wherever you want