import logging
import base64
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.content.models import CodeContent
from django.contrib.contenttypes.models import ContentType
from .models import SubscriptionPlan, CustomerSubscription, Cart, Order, DeveloperWallet, DeveloperTransaction, AdminWallet, AdminTransaction, CustomerWallet, CustomerTransaction
from apps.authentication.models import CustomerProfile
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from apps.authentication.views import role_required
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
import razorpay
from uuid import uuid4

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

logger = logging.getLogger(__name__)

def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'subscription_plans.html', {'plans': plans})

@login_required(login_url='login')
def subscribe(request, plan_id):
    user = request.user
    if user.role == 'developer':
        messages.warning(request, "Only customers can subscribe to plans.")
        return redirect('subscription_plans')

    plan = SubscriptionPlan.objects.get(pk=plan_id)
    existing = CustomerSubscription.objects.filter(customer=user, end_date__gte=timezone.now()).first()
    if existing:
        messages.info(request, "You already have an active subscription.")
        return redirect('subscription_plans')

    wallet, created = AdminWallet.objects.get_or_create(id=1)
    wallet.balance += plan.price
    wallet.save()

    AdminTransaction.objects.create(
        wallet=wallet,
        customer=user,
        plan=plan,
        amount=plan.price,
        status='completed'
    )

    CustomerSubscription.objects.create(
        customer=user,
        plan=plan,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=plan.duration_days)
    )
    
    profile, created = CustomerProfile.objects.get_or_create(user=user)
    profile.has_subscription = True
    profile.save()

    messages.success(request, f"You are now subscribed to {plan.name}!")
    return redirect('customer_dashboard')

@login_required(login_url='login')
def add_to_cart(request, model_type, object_id):
    if request.user.role != 'customer':
        return redirect('home')

    try:
        model = {'subscription': SubscriptionPlan, 'code': CodeContent}[model_type]
    except KeyError:
        messages.error(request, "Invalid item type.")
        return redirect('home')

    content_type = ContentType.objects.get_for_model(model)
    obj = get_object_or_404(model, id=object_id)
    existing = Cart.objects.filter(customer=request.user, content_type=content_type, object_id=obj.id).first()

    if not existing:
        Cart.objects.create(customer=request.user, content_type=content_type, object_id=obj.id)
        messages.success(request, "Item added to cart.")


    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='login')
def view_cart(request):
    if request.user.role != 'customer':
        return redirect('home')

    cart_items = Cart.objects.filter(customer=request.user)
    total_price = 0
    items_data = []
    for item in cart_items:
        content_object = item.content_object
        item_type = item.content_type.model
        price = getattr(content_object, 'price', 0)
        items_data.append({
            'type': item_type,
            'name': getattr(content_object, 'name', str(content_object)),
            'price': price,
            'id': item.object_id,
            'cart_id': item.id,
            'content_object': content_object,
        })
        total_price += price

    return render(request, 'cart.html', {'items': items_data, 'total_price': total_price})

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, customer=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

@login_required(login_url='login')
def confirm_payment(request):
    if request.user.role != 'customer':
        return redirect('home')

    cart_items = Cart.objects.filter(customer=request.user)
    total_price = sum(item.content_object.price for item in cart_items if hasattr(item.content_object, 'price'))
    items_data = []
    for item in cart_items:
        content_object = item.content_object
        item_type = item.content_type.model
        price = getattr(content_object, 'price', 0)
        items_data.append({
            'type': item_type,
            'name': getattr(content_object, 'name', str(content_object)),
            'price': price,
            'id': item.object_id,
            'content_object': content_object,
        })

    return render(request, 'confirm_payment.html', {'items': items_data, 'total_price': total_price})

@require_POST
@login_required(login_url='login')
def process_payment(request):
    if request.user.role != 'customer':
        return redirect('home')

    payment_method = request.POST.get('payment_method')
    if payment_method == 'saved_card':
        cart_items = Cart.objects.filter(customer=request.user)
        data = _process_checkout(request.user)
        if data['success']:
            Cart.objects.filter(customer=request.user).delete()
            recent_orders = [order.id for order in Order.objects.filter(customer=request.user).order_by('-purchased_at')[:len(cart_items)]]
            request.session['recent_orders'] = recent_orders
            request.session.modified = True  # Ensure session is saved
            logger.info(f"process_payment: Set recent_orders to {recent_orders} for user {request.user.username}")
            return redirect('payment_confirmed')
        else:
            logger.error(f"process_payment: Checkout failed for user {request.user.username}: {data.get('error')}")
            messages.error(request, "Payment failed.")
            return redirect('confirm_payment')
    else:
        messages.error(request, "Invalid payment method.")
        return redirect('confirm_payment')

def simulate_download_links(code_id):
    base = "/media/generated_files/"
    return {
        "html": f"{base}{code_id}_template.html",
        "css": f"{base}{code_id}_styles.css",
        "js": f"{base}{code_id}_script.js"
    }

def _process_checkout(user):
    cart_items = Cart.objects.filter(customer=user)
    logger.info(f"_process_checkout: Processing {len(cart_items)} cart items for user {user.username}")

    code_items = []
    has_subscription = False
    total_price = Decimal('0.00')
    subscription_data = None
    now = timezone.now()
    for item in cart_items:
        obj = item.content_object
        price = getattr(obj, 'price', Decimal('0.00'))
        if price is None:
            price = Decimal('0.00')
        logger.info(f"_process_checkout: Creating order for item {obj} with price {price}")
        Order.objects.create(
            customer=user,
            content_type=item.content_type,
            object_id=item.object_id,
            price=price
        )
        if isinstance(obj, SubscriptionPlan):
            sub, created = CustomerSubscription.objects.update_or_create(
                customer=user,
                defaults={
                    'plan': obj,
                    'start_date': now,
                    'end_date': now + timedelta(days=obj.duration_days),
                }
            )
            wallet, created = AdminWallet.objects.get_or_create(id=1)
            if isinstance(wallet.balance, float):
                wallet.balance = Decimal(str(wallet.balance))
            wallet.balance += price
            wallet.save()
            AdminTransaction.objects.create(
                wallet=wallet,
                customer=user,
                plan=obj,
                amount=price,
                status='completed'
            )
            has_subscription = True
            subscription_data = {'name': obj.name, 'price': float(price)}
        elif isinstance(obj, CodeContent):
            developer = obj.developer
            wallet, created = DeveloperWallet.objects.get_or_create(developer=developer)
            wallet.balance += price
            wallet.save()
            DeveloperTransaction.objects.create(
                wallet=wallet,
                customer=user,
                code_content=obj,
                amount=price,
                status='completed'
            )
            code_items.append({
                'title': obj.title,
                'price': float(price),
                'downloads': {
                    'html': f"data:text/html;base64,{base64.b64encode(obj.html_code.encode()).decode()}" if obj.html_code else '',
                    'css': f"data:text/css;base64,{base64.b64encode(obj.css_code.encode()).decode()}" if obj.css_code else '',
                    'js': f"data:text/javascript;base64,{base64.b64encode(obj.js_code.encode()).decode()}" if obj.js_code else '',
                }
            })
        total_price += price
    
    logger.info(f"_process_checkout: Completed for user {user.username}. Total price: {total_price}, Orders created: {len(cart_items)}")
    return {
        'success': True,
        'has_subscription': has_subscription,
        'has_code': bool(code_items),
        'subscription': subscription_data,
        'code_items': code_items,
        'total_price': float(total_price),
    }

@require_POST
@login_required(login_url='login')
def checkout(request):

    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'error': 'Only customers can checkout'}, status=403)

    try:
        data = _process_checkout(request.user)
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_POST
def initiate_razorpay(request):
    preview = _process_checkout(request.user)
    amount_paise = int(preview['total_price'] * 100)

    rzp_order = razorpay_client.order.create({
        'amount':       amount_paise,
        'currency':     'INR',
        'receipt':      f"rcptid_{request.user.id}_{timezone.now().timestamp()}",
        'payment_capture': '0',
    })

    return JsonResponse({
        'order_id': rzp_order['id'],
        'key':      settings.RAZORPAY_KEY_ID,
        'amount':   amount_paise,
        'currency': 'INR',
    })

@csrf_exempt
@login_required
@require_POST
def razorpay_callback(request):
    logger.info(f"razorpay_callback: Processing for user {request.user.username if request.user.is_authenticated else 'anonymous'}")
    params = {
        'razorpay_order_id': request.POST['razorpay_order_id'],
        'razorpay_payment_id': request.POST['razorpay_payment_id'],
        'razorpay_signature': request.POST['razorpay_signature'],
    }
    try:
        razorpay_client.utility.verify_payment_signature(params)
    except razorpay.errors.SignatureVerificationError:
        logger.error(f"razorpay_callback: Signature verification failed for user {request.user.username}")
        return JsonResponse({'success': False, 'error': 'Verification failed'}, status=400)

    try:
        order = razorpay_client.order.fetch(params['razorpay_order_id'])
        amount = order['amount']
    except Exception as e:
        logger.error(f"razorpay_callback: Failed to fetch order for user {request.user.username}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to fetch order details'}, status=500)

    try:
        razorpay_client.payment.capture(params['razorpay_payment_id'], amount)
    except Exception as e:
        logger.error(f"razorpay_callback: Failed to capture payment for user {request.user.username}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to capture payment'}, status=500)

    cart_items = Cart.objects.filter(customer=request.user)
    data = _process_checkout(request.user)
    if data['success']:
        Cart.objects.filter(customer=request.user).delete()
        recent_orders = [order.id for order in Order.objects.filter(customer=request.user).order_by('-purchased_at')[:len(cart_items)]]
        request.session['recent_orders'] = recent_orders
        request.session.modified = True
        logger.info(f"razorpay_callback: Set recent_orders to {recent_orders} for user {request.user.username}")
        return JsonResponse({'success': True, 'redirect_url': reverse('payment_confirmed')})
    else:
        logger.error(f"razorpay_callback: Checkout failed for user {request.user.username}: {data.get('error')}")
        return JsonResponse({'success': False, 'error': 'Checkout failed'}, status=500)

@login_required(login_url='login')
def payment_confirmed(request):
    orders = Order.objects.filter(customer=request.user).order_by('-purchased_at')[:1]
    total_price = sum(order.price for order in orders if order.price is not None)
    logger.info(f"payment_confirmed: Found {len(orders)} orders with total_price {total_price} for user {request.user.username}")
    return render(request, 'payment_confirmed.html', {'orders': orders, 'total_price': total_price})

@login_required(login_url='login')
@staff_member_required
def admin_wallet(request):
    wallet, created = AdminWallet.objects.get_or_create()
    transactions = AdminTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'admin_wallet.html', {
        'wallet': wallet,
        'transactions': transactions
        })


@login_required(login_url='login')
@role_required(allowed_roles=['developer'])
def developer_wallet(request):
    wallet, created = DeveloperWallet.objects.get_or_create(developer=request.user)
    transactions = DeveloperTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'developer_wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required(login_url='login')
def manage_subscription(request):
    user = request.user
    subscription = None
    if user.role == 'customer':
        try:
            subscription = CustomerSubscription.objects.get(customer=user)
        except CustomerSubscription.DoesNotExist:
            subscription = None
    return render(request, 'manage_subscription.html', {'subscription': subscription})

def customer_has_subscription(user):
    if hasattr(user, 'subscription'):
        return user.subscription.has_active_subscription()
    return False

@login_required(login_url='login')
def order_history(request):
    if request.user.role != 'customer':
        return redirect('home')

    wallet, created = CustomerWallet.objects.get_or_create(customer=request.user)

    orders = Order.objects.filter(customer=request.user).order_by('-purchased_at')

    wallet_balance = wallet.balance

    transactions = CustomerTransaction.objects.filter(wallet=wallet).order_by('-created_at')

    return render(request, 'customer_wallet.html', {
        'orders': orders,
        'wallet_balance': wallet_balance,
        'transactions': transactions,
    })

@require_POST
@login_required(login_url='login')
def add_money_to_wallet(request):
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Only customers can add money.'}, status=403)

    amount = request.POST.get('amount')
    try:
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except:
        return JsonResponse({'success': False, 'message': 'Invalid amount.'}, status=400)

    wallet, _ = CustomerWallet.objects.get_or_create(customer=request.user)
    wallet.balance += amount
    wallet.save()

    CustomerTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='deposit',
        description="Wallet top-up via Add Money"
    )

    return JsonResponse({'success': True, 'new_balance': float(wallet.balance)})

@require_POST
@login_required(login_url='login')
def initiate_wallet_payment(request):
    """Create a Razorpay order for the wallet top-up amount."""
    if request.user.role != 'customer':
        return JsonResponse({'success': False, 'message': 'Only customers can add money.'}, status=403)

    try:
        amount = Decimal(request.POST['amount'])
        if amount <= 0:
            raise ValueError
    except:
        return JsonResponse({'success': False, 'message': 'Invalid amount.'}, status=400)

    short_id = uuid4().hex[:8]
    receipt_id = f"wt_{request.user.id}_{short_id}"

    razor_amount = int(amount * 100)
    razor_order = razorpay_client.order.create({
        'amount': razor_amount,
        'currency': 'INR',
        'receipt': receipt_id,
        'payment_capture': 1
    })

    return JsonResponse({
        'success': True,
        'key': settings.RAZORPAY_KEY_ID,
        'order_id': razor_order['id'],
        'amount': razor_order['amount'],
        'currency': razor_order['currency'],
    })

@csrf_exempt
@require_POST
@login_required(login_url='login')
def wallet_payment_callback(request):
    """Verify Razorpay signature, then credit wallet."""
    payload = request.POST
    params = {
        'razorpay_order_id': payload.get('razorpay_order_id'),
        'razorpay_payment_id': payload.get('razorpay_payment_id'),
        'razorpay_signature': payload.get('razorpay_signature'),
    }
    try:
        razorpay_client.utility.verify_payment_signature(params)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'success': False, 'message': 'Signature verification failed.'}, status=400)

    amount = Decimal(request.POST.get('amount'))
    wallet, _ = CustomerWallet.objects.get_or_create(customer=request.user)
    wallet.balance += amount
    wallet.save()

    CustomerTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='deposit',
        description="Wallet top-up via Razorpay"
    )

    return JsonResponse({'success': True, 'new_balance': float(wallet.balance)})

@login_required(login_url='login')
def chat_with_developer(request, developer_id):
    if not request.user.customerprofile.has_subscription:
        messages.error(request, "You need a subscription to chat with developers.")
        return redirect('subscription_plans')
    return render(request, 'chat.html')