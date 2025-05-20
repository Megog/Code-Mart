from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomerProfile, DeveloperProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff:  # Assume staff users are developers
            DeveloperProfile.objects.create(user=instance)
        else:
            CustomerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'customerprofile'):
        instance.customerprofile.save()
    elif hasattr(instance, 'developerprofile'):
        instance.developerprofile.save()
