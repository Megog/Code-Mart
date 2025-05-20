import logging
import zipfile
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.files.storage import default_storage
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from apps.content.models import CodeContent
from .models import ChatThread, ChatMessage, ModificationRequest
from apps.billing.models import CustomerWallet, CustomerTransaction, AdminWallet, AdminTransaction, DeveloperWallet, DeveloperTransaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, DecimalException

logger = logging.getLogger(__name__)

@login_required
def chat_view(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    if request.user not in [thread.customer, thread.developer] and not request.user.is_staff:
        messages.error(request, "You don’t have access to this chat.")
        return redirect('home')

    mod_request, created = ModificationRequest.objects.get_or_create(thread=thread)
    messages_list = thread.messages.order_by('sent_at')

    if request.method == 'POST':
        # logger.info(f"POST request received for thread {thread_id} by {request.user.username}: {request.POST}")

        if 'set_price' in request.POST and request.user == thread.developer:
            price = request.POST.get('price')
            if price and price.strip():
                try:
                    price_decimal = Decimal(price)
                    if mod_request.status == 'pending':
                        mod_request.proposed_price = price_decimal
                        mod_request.status = 'negotiating'
                    elif mod_request.status == 'negotiating':
                        mod_request.proposed_price = price_decimal
                        mod_request.counter_price = None
                    mod_request.save()
                    ChatMessage.objects.create(
                        thread=thread,
                        sender=request.user,
                        message=f"Proposed price: ₹{price_decimal}. Please accept or propose a counter-offer."
                    )
                except (ValueError, DecimalException) as e:
                    logger.error(f"Invalid price: {price}, Error: {e}")
                    messages.error(request, "Please enter a valid price.")
            else:
                messages.error(request, "Price cannot be empty.")
            return redirect('chat_view', thread_id=thread.id)

        elif 'counter_price' in request.POST and request.user == thread.customer and mod_request.status == 'negotiating':
            counter_values = [v for v in request.POST.getlist('counter_price') if v.strip()]
            counter = counter_values[0] if counter_values else None
            # logger.info(f"Counter price submitted: {counter} (from values: {request.POST.getlist('counter_price')})")
            if counter:
                try:
                    counter_decimal = Decimal(counter)
                    if counter_decimal > mod_request.proposed_price:
                        messages.error(request, f"Counter-offer (₹{counter_decimal}) cannot exceed the proposed price (₹{mod_request.proposed_price}).")
                    else:
                        mod_request.counter_price = counter_decimal
                        mod_request.save()
                        ChatMessage.objects.create(
                            thread=thread,
                            sender=request.user,
                            message=f"Counter-offer: ₹{counter_decimal}. Please accept or propose a new price."
                        )
                except (ValueError, DecimalException) as e:
                    logger.error(f"Invalid counter price: {counter}, Error: {e}")
                    messages.error(request, "Please enter a valid counter-offer.")
            else:
                messages.error(request, "Counter-offer cannot be empty.")
            return redirect('chat_view', thread_id=thread.id)

        elif 'accept_proposed' in request.POST and request.user == thread.customer and mod_request.status == 'negotiating':
            mod_request.final_price = mod_request.proposed_price
            mod_request.status = 'price_confirmed'
            mod_request.save()
            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                message=f"Accepted proposed price of ₹{mod_request.final_price}. Please proceed with advance payment."
            )
            return redirect('chat_view', thread_id=thread.id)

        elif 'confirm_counter' in request.POST and request.user == thread.developer and mod_request.status == 'negotiating' and mod_request.counter_price:
            mod_request.final_price = mod_request.counter_price
            mod_request.status = 'price_confirmed'
            mod_request.save()
            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                message=f"Accepted counter-offer of ₹{mod_request.final_price}. Please proceed with advance payment."
            )
            return redirect('chat_view', thread_id=thread.id)

        elif 'pay_advance' in request.POST and request.user == thread.customer and mod_request.status == 'price_confirmed':
            advance = mod_request.final_price * Decimal('0.5')
            customer_wallet = request.user.customer_wallet
            admin_wallet, _ = AdminWallet.objects.get_or_create(id=1)

            if mod_request.advance_payment:
                messages.error(request, "Advance payment has already been made for this thread.")
                return redirect('chat_view', thread_id=thread.id)

            if customer_wallet.balance < advance:
                messages.error(request, f"Insufficient funds. You need ₹{advance}, but your balance is ₹{customer_wallet.balance}.")
            else:
                try:
                    with transaction.atomic():
                        customer_wallet.balance -= advance
                        customer_wallet.save()
                        CustomerTransaction.objects.create(
                            wallet=customer_wallet,
                            amount=advance,
                            transaction_type='withdrawal',
                            description=f"Advance payment for modification request {thread_id}"
                        )
                        admin_wallet.balance += advance
                        admin_wallet.save()
                        AdminTransaction.objects.create(
                            wallet=admin_wallet,
                            customer=request.user,
                            amount=advance,
                            description=f"Advance payment received for modification request {thread_id}"
                        )
                        mod_request.advance_payment = advance
                        mod_request.status = 'advance_paid'
                        mod_request.save()
                        ChatMessage.objects.create(
                            thread=thread,
                            sender=request.user,
                            message=f"Advance payment of ₹{advance} made."
                        )
                        messages.success(request, f"Advance payment of ₹{advance} successfully processed.")
                except Exception as e:
                    logger.error(f"Payment failed for thread {thread_id}: {str(e)}")
                    messages.error(request, "Payment failed. Please try again or contact support.")
            return redirect('chat_view', thread_id=thread.id)

        elif 'upload_code' in request.POST and request.user == thread.developer and mod_request.status == 'advance_paid':
            attachment = request.FILES.get('attachment')
            if not attachment:
                messages.error(request, "Please upload a file.")
            elif not attachment.name.endswith('.zip'):
                messages.error(request, "Please upload a .zip file.")
            else:
                file_path = default_storage.save(f'chat_attachments/{thread_id}/{attachment.name}', attachment)
                absolute_file_path = default_storage.path(file_path)
                zip_ref = zipfile.ZipFile(absolute_file_path, 'r')
                try:
                    file_list = zip_ref.namelist()
                    index_path = None
                    for file_name in file_list:
                        if file_name.endswith('index.html'):
                            index_path = file_name
                            break
                    if not index_path:
                        messages.error(request, "Zip must contain an 'index.html' file.")
                        zip_ref.close()
                        try:
                            default_storage.delete(file_path)
                        except PermissionError as e:
                            logger.warning(f"Could not delete {file_path} due to {e}.")
                    else:
                        mod_request.uploaded_file = file_path
                        mod_request.status = 'code_delivered'
                        mod_request.preview_token = get_random_string(32)
                        mod_request.save()
                        logger.info(f"Thread {thread_id} status updated to 'code_delivered' by {request.user.username}")
                        messages.success(request, "Modified code uploaded successfully.")
                finally:
                    zip_ref.close()
            return redirect('chat_view', thread_id=thread.id)

        elif 'decline_deal' in request.POST and request.user == thread.developer and mod_request.status == 'negotiating':
            mod_request.status = 'declined'
            mod_request.save()
            thread.is_active = False
            thread.save()
            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                message="Deal declined. Chat thread closed."
            )
            return redirect('developer_dashboard')

        elif 'confirm_satisfaction' in request.POST and request.user == thread.customer and mod_request.status == 'code_delivered':
            remaining_payment = mod_request.final_price - mod_request.advance_payment
            customer_wallet = request.user.customer_wallet
            admin_wallet, _ = AdminWallet.objects.get_or_create(id=1)
            developer_wallet, _ = DeveloperWallet.objects.get_or_create(developer=thread.developer)

            if customer_wallet.balance < remaining_payment:
                messages.error(request, f"Insufficient funds. You need ₹{remaining_payment}, but your balance is ₹{customer_wallet.balance}.")
            else:
                try:
                    with transaction.atomic():
                        customer_wallet.balance -= remaining_payment
                        customer_wallet.save()
                        CustomerTransaction.objects.create(
                            wallet=customer_wallet,
                            amount=remaining_payment,
                            transaction_type='withdrawal',
                            description=f"Final payment for modification request {thread_id}"
                        )
                        admin_wallet.balance += remaining_payment
                        admin_wallet.save()
                        AdminTransaction.objects.create(
                            wallet=admin_wallet,
                            customer=request.user,
                            amount=remaining_payment,
                            description=f"Final payment received for modification request {thread_id}"
                        )
                        mod_request.full_payment = remaining_payment
                        mod_request.save()

                        total_amount = mod_request.final_price
                        if admin_wallet.balance < total_amount:
                            raise Exception("Admin wallet has insufficient funds to transfer to developer.")
                        admin_wallet.balance -= total_amount
                        admin_wallet.save()
                        AdminTransaction.objects.create(
                            wallet=admin_wallet,
                            customer=request.user,
                            amount=total_amount,
                            description=f"Transferred full payment to developer for modification request {thread_id}"
                        )
                        developer_wallet.balance += total_amount
                        developer_wallet.save()
                        DeveloperTransaction.objects.create(
                            wallet=developer_wallet,
                            customer=request.user,
                            code_content=thread.code_content,
                            amount=total_amount,
                            description=f"Payment for modification request {thread_id}"
                        )

                        mod_request.status = 'completed'
                        mod_request.save()
                        ChatMessage.objects.create(
                            thread=thread,
                            sender=request.user,
                            message=f"Final payment of ₹{remaining_payment} made. Full amount (₹{total_amount}) transferred to developer. Modification request completed."
                        )
                        messages.success(request, f"Satisfaction confirmed. Full payment of ₹{total_amount} processed to developer.")
                except Exception as e:
                    logger.error(f"Final payment failed for thread {thread_id}: {str(e)}")
                    messages.error(request, "Payment failed. Please try again or contact support.")
            return redirect('chat_view', thread_id=thread.id)

        elif 'raise_dispute' in request.POST and request.user == thread.customer and mod_request.status == 'code_delivered':
            dispute_reason = request.POST.get('dispute_reason')
            if not dispute_reason or not dispute_reason.strip():
                messages.error(request, "Please provide a reason for the dispute.")
            else:
                mod_request.status = 'disputed'
                mod_request.dispute_reason = dispute_reason
                mod_request.save()
                thread.flagged_for_review = True
                thread.save()
                ChatMessage.objects.create(
                    thread=thread,
                    sender=request.user,
                    message=f"Dispute raised: {dispute_reason}"
                )
                messages.success(request, "Dispute raised successfully. An admin will review it soon.")
            return redirect('chat_view', thread_id=thread.id)

        else:
            message = request.POST.get('message')
            attachment = request.FILES.get('attachment')
            if message or attachment:
                ChatMessage.objects.create(
                    thread=thread,
                    sender=request.user,
                    message=message,
                    attachment=attachment
                )
            return redirect('chat_view', thread_id=thread.id)

    if request.user == thread.customer or request.user == thread.developer:
        thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    advance_amount = mod_request.final_price / Decimal('2') if mod_request.final_price else None
    remaining_amount = (mod_request.final_price - mod_request.advance_payment) if (mod_request.final_price and mod_request.advance_payment) else None

    return render(request, 'chat.html', {
        'thread': thread,
        'chat_messages': messages_list,
        'mod_request': mod_request,
        'advance_amount': advance_amount,
        'remaining_amount': remaining_amount,
        'wallet_balance': request.user.customer_wallet.balance if request.user.role == 'customer' else None
    })

@require_GET
@xframe_options_exempt
@login_required
def preview_code(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    
    if request.user not in [thread.customer, thread.developer] and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
    
    mod_request = thread.modificationrequest
    token = request.GET.get('token')

    if not request.user.is_staff:
        if mod_request.status != 'code_delivered' or (request.user == thread.customer and token != mod_request.preview_token):
            return HttpResponse("No preview available or invalid token", status=404)
        
        if request.user == thread.customer:
            if mod_request.customer_preview_count >= 3:
                return HttpResponse("Preview limit reached (3 times).", status=403)
            mod_request.customer_preview_count += 1
            mod_request.save()
        elif request.user == thread.developer:
            mod_request.developer_preview_count += 1
            mod_request.save()

    if not mod_request.uploaded_file:
        return HttpResponse("No file uploaded", status=404)

    file_path = default_storage.path(mod_request.uploaded_file.name)
    extract_path = default_storage.path(f'tmp/preview/{thread_id}')
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    index_html_path = None
    for root, dirs, files in os.walk(extract_path):
        if 'index.html' in files:
            index_html_path = os.path.join(root, 'index.html')
            break
    
    if not index_html_path:
        return HttpResponse("No index.html found in zip", status=404)
    
    with open(index_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    base_url = f"/media/tmp/preview/{thread_id}/"
    if 'glowing button' in index_html_path:
        base_url += "glowing button/"
    html_content = html_content.replace('styles.css', base_url + 'styles.css')
    
    return HttpResponse(html_content, content_type='text/html')

@login_required
def download_code(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    if request.user != thread.customer:
        return HttpResponse("Unauthorized", status=403)
    
    mod_request = thread.modificationrequest
    if mod_request.status != 'completed' or not mod_request.uploaded_file:
        return HttpResponse("Download not available", status=404)
    
    file_path = default_storage.path(mod_request.uploaded_file.name)
    if not os.path.exists(file_path):
        return HttpResponse("File not found", status=404)
    
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    return response

@staff_member_required
def admin_chat_view(request, thread_id=None):
    if request.method == 'POST' and thread_id:
        thread = get_object_or_404(ChatThread, id=thread_id)
        mod_request = thread.modificationrequest

        if 'message' in request.POST:
            message = request.POST.get('message')
            attachment = request.FILES.get('attachment')
            if message or attachment:
                ChatMessage.objects.create(
                    thread=thread,
                    sender=request.user,
                    message=message,
                    attachment=attachment
                )
                messages.success(request, "Message sent successfully.")
            return redirect('admin_chat_view', thread_id=thread.id)

        elif 'resolve_dispute' in request.POST and mod_request.status == 'disputed':
            action = request.POST.get('action')
            warning_target = request.POST.get('warning_target')
            admin_wallet, _ = AdminWallet.objects.get_or_create(id=1)

            if action == 'refund':
                try:
                    with transaction.atomic():
                        customer_wallet = thread.customer.customer_wallet
                        refund_amount = mod_request.advance_payment
                        if admin_wallet.balance < refund_amount:
                            raise Exception("Admin wallet has insufficient funds to issue refund.")
                        
                        admin_wallet.balance -= refund_amount
                        admin_wallet.save()
                        AdminTransaction.objects.create(
                            wallet=admin_wallet,
                            customer=thread.customer,
                            amount=refund_amount,
                            description=f"Refund issued for disputed modification request {thread_id}"
                        )
                        customer_wallet.balance += refund_amount
                        customer_wallet.save()
                        CustomerTransaction.objects.create(
                            wallet=customer_wallet,
                            amount=refund_amount,
                            transaction_type='deposit',
                            description=f"Refund received for disputed modification request {thread_id}"
                        )
                        mod_request.status = 'refunded'
                        mod_request.save()
                        thread.flagged_for_review = False
                        thread.is_active = False
                        thread.save()
                        ChatMessage.objects.create(
                            thread=thread,
                            sender=request.user,
                            message=f"Dispute resolved: Customer refunded ₹{refund_amount}. Thread closed."
                        )
                        messages.success(request, f"Dispute resolved. Customer refunded ₹{refund_amount}.")
                except Exception as e:
                    logger.error(f"Refund failed for thread {thread_id}: {str(e)}")
                    messages.error(request, "Refund failed. Please try again or check admin wallet balance.")

            elif action == 'pay_developer':
                try:
                    with transaction.atomic():
                        developer_wallet, _ = DeveloperWallet.objects.get_or_create(developer=thread.developer)
                        total_amount = mod_request.final_price
                        if admin_wallet.balance < total_amount:
                            raise Exception("Admin wallet has insufficient funds to pay developer.")
                        
                        admin_wallet.balance -= total_amount
                        admin_wallet.save()
                        AdminTransaction.objects.create(
                            wallet=admin_wallet,
                            customer=thread.customer,
                            amount=total_amount,
                            description=f"Transferred full payment to developer for disputed modification request {thread_id}"
                        )
                        developer_wallet.balance += total_amount
                        developer_wallet.save()
                        DeveloperTransaction.objects.create(
                            wallet=developer_wallet,
                            customer=thread.customer,
                            code_content=thread.code_content,
                            amount=total_amount,
                            description=f"Payment for disputed modification request {thread_id}"
                        )
                        mod_request.status = 'closed'
                        mod_request.save()
                        thread.flagged_for_review = False
                        thread.is_active = False
                        thread.save()
                        ChatMessage.objects.create(
                            thread=thread,
                            sender=request.user,
                            message=f"Dispute resolved: Developer paid full amount ₹{total_amount}. Thread closed."
                        )
                        messages.success(request, f"Dispute resolved. Developer paid ₹{total_amount}.")
                except Exception as e:
                    logger.error(f"Payment to developer failed for thread {thread_id}: {str(e)}")
                    messages.error(request, "Payment failed. Please try again or check admin wallet balance.")

            elif action == 'resume':
                if not warning_target:
                    messages.error(request, "Please select a target for the warning.")
                else:
                    target_user = thread.developer if warning_target == 'developer' else thread.customer
                    mod_request.status = 'code_delivered'
                    mod_request.save()
                    thread.flagged_for_review = False
                    thread.save()
                    ChatMessage.objects.create(
                        thread=thread,
                        sender=request.user,
                        message=f"Dispute resolved: Chat resumed with a warning to {target_user.username}. Please address the issue."
                    )
                    messages.success(request, f"Chat resumed with a warning to {target_user.username}.")
            
            return redirect('admin_chat_view', thread_id=thread.id)

    if not thread_id:
        threads = ChatThread.objects.all().order_by('-created_at')
        return render(request, 'admin_chat.html', {
            'threads': threads,
            'selected_thread': None,
        })

    thread = get_object_or_404(ChatThread, id=thread_id)
    mod_request = thread.modificationrequest
    messages_list = thread.messages.order_by('sent_at')
    advance_amount = mod_request.final_price / Decimal('2') if mod_request.final_price else None
    remaining_amount = (mod_request.final_price - mod_request.advance_payment) if (mod_request.final_price and mod_request.advance_payment) else None

    return render(request, 'admin_chat.html', {
        'threads': ChatThread.objects.all().order_by('-created_at'),
        'selected_thread': thread,
        'chat_messages': messages_list,
        'mod_request': mod_request,
        'advance_amount': advance_amount,
        'remaining_amount': remaining_amount,
    })

def initiate_chat(request, code_id):
    code_content = get_object_or_404(CodeContent, id=code_id)
    developer = code_content.developer

    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to request modifications.")
        return redirect('login')

    if request.user.role != 'customer':
        messages.error(request, "Only customers can request modifications.")
        return redirect('code_detail', code_id=code_id)

    if not request.user.customerprofile.has_subscription:
        messages.warning(request, "You need an active subscription to request modifications.")
        return redirect('subscription_plans')

    customer = request.user
    thread = ChatThread.objects.filter(
        customer=customer,
        developer=developer,
        code_content=code_content,
        is_active=True
    ).first()

    if not thread:
        thread = ChatThread.objects.create(
            customer=customer,
            developer=developer,
            code_content=code_content
        )
        ChatMessage.objects.create(
            thread=thread,
            sender=customer,
            message=f"{customer.username} has requested a modification for {code_content.title}."
        )
        ModificationRequest.objects.create(thread=thread)

    return redirect('chat_view', thread_id=thread.id)

@login_required
def notifications(request):
    notifications = []
    unread_count = 0

    if request.user.role == 'customer':
        if request.user.customerprofile.has_subscription:
            unread_messages = ChatMessage.objects.filter(
                thread__customer=request.user,
                is_read=False
            ).exclude(sender=request.user)
            unread_count = unread_messages.count()
            for message in unread_messages[:5]:
                notifications.append({
                    'message': f"New message from {message.sender.username} in {message.thread.code_content.title}",
                    'link': reverse('chat_view', args=[message.thread.id])
                })
        else:
            new_uploads = CodeContent.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            )[:5]
            unread_count = new_uploads.count()
            for upload in new_uploads:
                notifications.append({
                    'message': f"New upload: {upload.title} by {upload.developer.username}",
                    'link': reverse('content_detail', args=[upload.id])
                })
    elif request.user.role == 'developer':
        unread_messages = ChatMessage.objects.filter(
            thread__developer=request.user,
            is_read=False
        ).exclude(sender=request.user)
        unread_count = unread_messages.count()
        for message in unread_messages[:5]:
            notifications.append({
                'message': f"New message from {message.sender.username} in {message.thread.code_content.title}",
                'link': reverse('chat_view', args=[message.thread.id])
            })

    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications
    })

@login_required
def active_chats(request):
    if request.user.role not in ['customer', 'developer']:
        messages.error(request, "You don’t have access to this page.")
        return redirect('home')

    if request.user.role == 'customer':
        active_chats = ChatThread.objects.filter(customer=request.user).order_by('-created_at')
    else:  # developer
        active_chats = ChatThread.objects.filter(developer=request.user)

    context = {
        'active_chats': active_chats.order_by('-created_at'),
        'user_role': request.user.role,
    }
    return render(request, 'active_chats.html', context)
