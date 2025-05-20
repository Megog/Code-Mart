from django.db import models
from django.contrib.auth.models import User
from apps.content.models import CodeContent
from datetime import timedelta
from django.utils import timezone
from apps.authentication.models import CustomerProfile
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CustomerSubscription(models.Model):
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()

    def is_active(self):
        return self.end_date >= timezone.now()

    def __str__(self):
        return f"{self.customer.username}'s subscription"

    def save(self, *args, **kwargs):
        if self.plan and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

class Cart(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.content_type.name} - {self.content_object}"

User = get_user_model()

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    def __str__(self):
        return f"{self.customer.username} - {self.content_object} - {self.purchased_at.strftime('%Y-%m-%d %H:%M')}"

class DeveloperWallet(models.Model):
    developer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'developer'}
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.developer.username}'s Wallet - ₹{self.balance}"

class DeveloperTransaction(models.Model):
    wallet = models.ForeignKey(
        DeveloperWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'customer'}
    )
    code_content = models.ForeignKey(
        CodeContent,
        on_delete=models.SET_NULL,
        null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )

    def __str__(self):
        return f"{self.customer.username} bought {self.code_content.title} for ₹{self.amount}"
    
class AdminWallet(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Admin Wallet - ₹{self.balance}"

class AdminTransaction(models.Model):
    wallet = models.ForeignKey(
        AdminWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'customer'}
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )

    def __str__(self):
        customer_name = self.customer.username if self.customer else "Anonymous"
        if self.plan:
            return f"{customer_name} subscribed to {self.plan.name} for ₹{self.amount}"
        return f"{customer_name} - {self.description or 'No description'} - ₹{self.amount}"
    
class CustomerWallet(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'},
        related_name='customer_wallet'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.customer.username}'s Wallet - ₹{self.balance}"

class CustomerTransaction(models.Model):
    wallet = models.ForeignKey(
        CustomerWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=[('deposit', 'Deposit'), ('withdrawal', 'Withdrawal'), ('transfer', 'Transfer')],
        default='transfer'
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='completed'
    )

    def __str__(self):
        return f"{self.transaction_type} of ₹{self.amount} for {self.wallet.customer.username}"