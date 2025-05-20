from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User  # Ensure correct User model is used
from .models import CustomerProfile, DeveloperProfile

class SignUpForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)

    role = forms.ChoiceField(choices=[('developer', 'Developer'), ('customer', 'Customer')])

    first_name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'class': 're_input', 'placeholder': 'First Name'}
    ))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'class': 're_input', 'placeholder': 'Last Name'}
    ))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 're_input', 'placeholder': 'Email'}
    ))
    username = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'class': 're_input', 'placeholder': 'Username'}
    ))
    password1 = forms.CharField(max_length=100, widget=forms.PasswordInput(
        attrs={'class': 're_input', 'placeholder': 'Password'}
    ))
    password2 = forms.CharField(max_length=100, widget=forms.PasswordInput(
        attrs={'class': 're_input', 'placeholder': 'Confirm Password'}
    ))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'username', 'password1', 'password2', 'profile_picture']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'role': 'Role',
            'username': 'Username',
            'password1': 'Password',
            'password2': 'Confirm Password',
            'profile_picture': 'Profile Picture',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "re_input", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "re_input", "placeholder": "Password"})
    )

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'mobile', 'profile_picture']

class CustomerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['bio', 'city', 'state', 'country', 'website', 'github_link', 'linkedIn_link', 'x_link', 'instagram_link']

class DeveloperProfileUpdateForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter skills separated by commas'})
    )
    class Meta:
        model = DeveloperProfile
        fields = ['skills', 'portfolio_link', 'city', 'state', 'country', 'bio', 'website', 'github_link', 'linkedIn_link', 'x_link', 'instagram_link']

class UserProfilePictureUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["profile_picture"]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "custom-file-input"}),
        }