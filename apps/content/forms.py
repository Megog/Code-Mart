from django import forms
from .models import CodeContent

class CodeContentForm(forms.ModelForm):
    class Meta:
        model = CodeContent
        fields = ['title', 'description', 'html_code', 'css_code', 'js_code', 'price', 'image_preview', 'category', 'difficulty']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter title here...'}),
            'description': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Describe your code content here...'}),
            'html_code': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter HTML code here...'}),
            'css_code': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter CSS code here...'}),
            'js_code': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter JavaScript code here...'}),
        }