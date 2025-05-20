from django.db import models
from django.conf import settings
from apps.content.models import CodeContent
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatThread(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_chats',
        limit_choices_to={'role': 'customer'}
    )
    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='developer_chats',
        limit_choices_to={'role': 'developer'}
    )
    code_content = models.ForeignKey(
        CodeContent,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    flagged_for_review = models.BooleanField(default=False)

    def __str__(self):
        return f"Chat for {self.code_content.title} between {self.customer.username} and {self.developer.username}"

class ChatMessage(models.Model):
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    message = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to='chat_attachments/',
        blank=True,
        null=True
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender.username} in {self.thread}"

class ModificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('negotiating', 'Negotiating'),
        ('price_confirmed', 'Price Confirmed'),
        ('advance_paid', 'Advance Paid'),
        ('code_delivered', 'Code Delivered'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('declined', 'Declined'),
        ('refunded', 'Refunded'),
        ('closed', 'Closed'),  # New status for paid-to-developer dispute resolution
    ]
    thread = models.OneToOneField(ChatThread, on_delete=models.CASCADE)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    counter_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    full_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    preview_token = models.CharField(max_length=32, null=True, blank=True)
    customer_preview_count = models.IntegerField(default=0)
    developer_preview_count = models.IntegerField(default=0)
    uploaded_file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/', null=True, blank=True)
    dispute_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Modification for {self.thread.code_content.title}"
    
