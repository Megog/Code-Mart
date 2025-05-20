from django.shortcuts import render, redirect
from .forms import CodeContentForm
from .models import CodeContent
from apps.authentication.models import DeveloperProfile
from apps.billing.models import CustomerSubscription
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from apps.authentication.models import User
from django.urls import reverse
from django.utils import timezone


def rough(request):
    codes = CodeContent.objects.all().order_by('-created_at')
    return render(request, 'rough.html', {'codes': codes})

def welcome(request):
    codes = CodeContent.objects.all().order_by('-created_at')
    return render(request, 'welcome.html', {'codes': codes})

def about(request):
    return render(request, 'about.html')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def contact(request):
    return render(request, 'contact.html')

@login_required(login_url='login')
def upload_code(request):
    if not request.user.role == 'developer':
        messages.error(request, "Only developers can upload code.")
        return redirect('home')
    if request.method == "POST":
        form = CodeContentForm(request.POST, request.FILES)
        if form.is_valid():
            code = form.save(commit=False)
            code.developer = request.user
            code.save()            
            return redirect('developer_dashboard')
    else:
        form = CodeContentForm()
    return render(request, 'upload_code.html', {'form': form})

@login_required(login_url='login')
def update_content(request, pk):
    code = get_object_or_404(CodeContent, pk=pk, developer=request.user)
    
    if request.method == 'POST':
        form = CodeContentForm(request.POST, request.FILES, instance=code)
        if form.is_valid():
            form.save()
            return redirect('my_content')
    else:
        form = CodeContentForm(instance=code)
    
    return render(request, 'update_content.html', {'form': form})

def home(request):
    # codes = CodeContent.objects.all().order_by('-created_at')
    # return render(request, 'home.html', {'codes': codes})
    codes = CodeContent.objects.all().order_by('-created_at')
    paginator = Paginator(codes, 6)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home.html', {'codes': page_obj})

def my_content(request):
    codes = CodeContent.objects.filter(developer=request.user).order_by('-created_at')
    return render(request, 'my_content.html', {'codes': codes})

def code_detail(request, code_id):
    code = get_object_or_404(CodeContent, id=code_id)
    return render(request, 'code_detail.html', {'code': code})

class CategoryView(View):
    def get(self, request, val):
        valid_categories = CodeContent.objects.values_list('category', flat=True).distinct()
        if val not in valid_categories:
            return redirect('home')

        codes = CodeContent.objects.filter(category=val)

        paginator = Paginator(codes, 6)  # Show 6 code snippets per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        titles = codes.values('title')
        context = {
            'category': val,
            'codes': page_obj,
            'titles': titles
        }
        return render(request, "category.html", context)


@require_POST
@login_required(login_url='login')
def delete_content(request, pk):
    content = get_object_or_404(CodeContent, pk=pk, developer=request.user.developerprofile)
    content.delete()
    return redirect('my_content')

def developer_profile_view(request, username):
    developer = get_object_or_404(User, username=username)
    profile = get_object_or_404(DeveloperProfile, user=developer)
    code_contents = CodeContent.objects.filter(developer=developer)

    is_subscribed = False
    if request.user.is_authenticated and hasattr(request.user, 'customerprofile'):
        subscription = CustomerSubscription.objects.filter(
            customer=request.user,
            end_date__gte=timezone.now()
        ).first()
        if subscription:
            is_subscribed = True

    context = {
        "developer": developer,
        "profile": profile,
        "code_contents": code_contents,
        "is_subscribed": is_subscribed
    }
    return render(request, 'developers_profile.html', context)

def handler400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def handler403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def handler404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def handler500(request, exception=None):
    return render(request, 'errors/500.html', status=500)