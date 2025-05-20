from django.contrib import admin
from .models import CustomerProfile, DeveloperProfile, User

admin.site.register(CustomerProfile)
admin.site.register(DeveloperProfile)
admin.site.register(User)