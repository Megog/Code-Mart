from django.urls import path
from . import views

urlpatterns = [
    # Subscription Plans URLs Flow Control
    path('plans/', views.subscription_plans, name='subscription_plans'),

    # Subscribe Flow Control
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),

    # Dashboard Manage Subscription Flow Control
    path('dashboard/manage-subscription/', views.manage_subscription, name='manage_subscription'),

    # Add-to-Cart Flow Control
    path('add-to-cart/<str:model_type>/<int:object_id>/', views.add_to_cart, name='add_to_cart'),

    # View Cart Flow Control
    path('cart/', views.view_cart, name='cart'),

    # Remove-Item From Cart Flow Control
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),

    path('process-payment/', views.process_payment, name='process_payment'),

    path('payment-confirmed/', views.payment_confirmed, name='payment_confirmed'),
    # Checkout Flow Control
    path('checkout/', views.checkout, name='checkout'),

    path('razorpay/initiate/', views.initiate_razorpay, name='rz_initiate'),
    
    path('razorpay/callback/',  views.razorpay_callback, name='rz_callback'),
    
    # Order History Flow Control
    path('order-history/', views.order_history, name='order_history'),

    # Add Money to Wallet Flow Control
    path('add-money/', views.add_money_to_wallet, name='add_money_to_wallet'),

    path('wallet/initiate/', views.initiate_wallet_payment, name='initiate_wallet_payment'),
    
    path('wallet/callback/', views.wallet_payment_callback, name='wallet_payment_callback'),

    # Developer Wallet Flow Control
    path('developer/wallet/', views.developer_wallet, name='developer_wallet'),

    #Admin Wallet Flow Control
    path('admin/wallet/', views.admin_wallet, name='admin_wallet'),

]
