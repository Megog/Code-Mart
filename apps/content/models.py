from django.db import models
from apps.authentication.models import User  # Adjust based on your actual import path

class CodeContent(models.Model):
    developer = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    html_code = models.TextField()
    css_code = models.TextField(blank=True, null=True)
    js_code = models.TextField(blank=True, null=True)
    image_preview = models.ImageField(upload_to='code_previews/', blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    CATEGORY_CHOICES = [
        ('card', 'Cards'),
        ('checkbox', 'Checkbox'),
        ('button', 'Button'),
        ('switch', 'Switch'),
        ('form', 'Form'),
        ('toggle', 'Toggle'),
        ('input', 'Input'),
        ('slider', 'Slider'),
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio'),
        ('modal', 'Modal'),
        ('tabs', 'Tabs'),
        ('alert', 'Alert'),
        ('hover', 'Hover'),
        ('responsive', 'Responsive'),
        ('other', 'Other')
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.developer.username}"
