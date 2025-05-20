# Digital_Content_Marketplace/apps/billing/admin.py
from django.contrib import admin
from .models import (
    SubscriptionPlan, CustomerSubscription, Cart, Order, 
    DeveloperWallet, DeveloperTransaction, AdminWallet, AdminTransaction,
    CustomerWallet, CustomerTransaction
)

# Register SubscriptionPlan
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active')
    search_fields = ('name',)

# Register CustomerSubscription
@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'plan', 'start_date', 'end_date')
    search_fields = ('customer__username', 'plan__name')

# Register Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'content_type', 'object_id', 'content_object')
    search_fields = ('customer__username',)

# Register Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'purchased_at', 'price', 'status', 'content_type', 'content_object')
    search_fields = ('customer__username',)
    list_filter = ('purchased_at', 'content_type', 'status')
    date_hierarchy = 'purchased_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'content_type')

# Register DeveloperWallet
@admin.register(DeveloperWallet)
class DeveloperWalletAdmin(admin.ModelAdmin):
    list_display = ('developer', 'balance')
    search_fields = ('developer__username',)

# Register DeveloperTransaction
@admin.register(DeveloperTransaction)
class DeveloperTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'customer', 'code_content', 'amount', 'status', 'created_at')
    search_fields = ('customer__username', 'code_content__title')
    list_filter = ('status', 'created_at')

# Register AdminWallet
@admin.register(AdminWallet)
class AdminWalletAdmin(admin.ModelAdmin):
    list_display = ('balance',)
    readonly_fields = ('balance',)  # Prevent manual editing

# Register AdminTransaction (Updated)
@admin.register(AdminTransaction)
class AdminTransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'plan', 'amount', 'description', 'status', 'created_at')  # Added 'description'
    search_fields = ('customer__username', 'plan__name', 'description')  # Added 'description'
    list_filter = ('status', 'created_at')
    fields = ('wallet', 'customer', 'plan', 'amount', 'description', 'status', 'created_at')  # Make editable
    readonly_fields = ('created_at',)

# Register CustomerWallet (New)
@admin.register(CustomerWallet)
class CustomerWalletAdmin(admin.ModelAdmin):
    list_display = ('customer', 'balance')
    search_fields = ('customer__username',)
    readonly_fields = ('balance',)
    
    
# Register CustomerTransaction (New)
@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'description', 'status', 'created_at')
    search_fields = ('wallet__customer__username', 'description')
    list_filter = ('transaction_type', 'status', 'created_at')