from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.functional import cached_property
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('developer', 'Developer'),
        ('customer', 'Customer'),
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        default='profile_pics/user_default.png'
        )
    mobile = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    email = models.EmailField(max_length=50, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    REQUIRED_FIELDS = ['email', 'mobile']

    groups = models.ManyToManyField(Group, blank=True)
    user_permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        app_label = 'authentication'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

# Customer Profile Model
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    # Social Media Profile
    github_link = models.URLField(blank=True, null=True)
    linkedIn_link = models.URLField(blank=True, null=True)
    x_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    @cached_property
    def has_subscription(self):
        from apps.billing.models import CustomerSubscription
        now = timezone.now()
        return CustomerSubscription.objects.filter(
            customer=self.user,
            start_date__lte=now,
            end_date__gte=now
        ).exists()

    def __str__(self):
        return f"{self.user.username} - Customer"

# Developer Profile Model
class DeveloperProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.TextField(blank=True, help_text="List your skills separated by commas")
    portfolio_link = models.URLField(blank=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    # Social Media Profile
    github_link = models.URLField(blank=True, null=True)
    linkedIn_link = models.URLField(blank=True, null=True)
    x_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    def skill_list(self):
        """Returns a list of skills from a comma-separated string."""
        return self.skills.split(",") if self.skills else []
    def __str__(self):
        return f"{self.user.username} - Developer"