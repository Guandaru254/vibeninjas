"""
ZOZAPRIME Payment Views
========================
Location: payments/views.py (REPLACE existing file)
"""
import json
import logging
import uuid
import hmac
import hashlib

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction as db_transaction
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from events.models import Event, TicketCategory, Ticket, PromoCode
from .models import Transaction
from .services import MpesaService
from .paystack import checkout

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# INITIATE M-PESA STK PUSH
# ═══════════════════════════════════════════════════════════════════════════════
from decimal import Decimal

def initiate_mpesa_payment(request, slug):
    """
    Initiate M-Pesa STK Push payment with Promo Code support.
    """
    try:
        event = get_object_or_404(Event, slug=slug)

        buyer_name = request.POST.get('buyer_name', '').strip()
        buyer_email = request.POST.get('buyer_email', '').strip()
        buyer_phone = request.POST.get('buyer_phone', '').strip()
        category_id = request.POST.get('category_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # ══════════════════════════════════════════════════════════
        # 1. CAPTURE PROMO CODE
        # ══════════════════════════════════════════════════════════
        promo_code_str = request.POST.get('promo_code_used') or request.session.get('promo_code')

        if not all([buyer_name, buyer_email, buyer_phone, category_id]):
            return JsonResponse({'success': False, 'error': 'All fields are required'})

        # Format phone to 254XXXXXXXXX
        phone = buyer_phone.replace('+', '').replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        if not phone.startswith('254') or len(phone) != 12:
            return JsonResponse({
                'success': False,
                'error': 'Invalid phone number. Use format: 0712345678'
            })

        category = get_object_or_404(TicketCategory, id=category_id, event=event)

        if category.is_free:
            return JsonResponse({
                'success': False,
                'error': 'This is a free ticket. Please use the RSVP flow.'
            }, status=400)

        if category.available_tickets < quantity:
            return JsonResponse({
                'success': False,
                'error': f'Only {category.available_tickets} tickets available'
            })

        # Base calculation
        unit_price = Decimal(str(category.effective_price))
        total_amount = unit_price * quantity

        # ══════════════════════════════════════════════════════════
        # 2. SERVER-SIDE PROMO VALIDATION (Security Check)
        # ══════════════════════════════════════════════════════════
        if promo_code_str:
            try:
                promo = PromoCode.objects.get(code=promo_code_str.upper().strip(), is_active=True)
                # Validate against this specific event
                is_valid, _ = promo.validate(event=event)
                
                if is_valid:
                    if promo.discount_type == 'percentage':
                        discount = (promo.discount_value / Decimal('100')) * total_amount
                    else:
                        discount = promo.discount_value
                    
                    total_amount = max(total_amount - discount, Decimal('0'))
                    logger.info(f"[STK] Promo Applied: {promo_code_str}. New Total: {total_amount}")
            except PromoCode.DoesNotExist:
                logger.warning(f"[STK] Attempted invalid promo: {promo_code_str}")

        # Final safety check for M-Pesa (Must be at least 1 bob)
        if total_amount <= 0:
            total_amount = Decimal('1') 

        callback_url = settings.MPESA_CALLBACK_URL
        logger.info(f"[STK] Phone: {phone}, Amount: {total_amount}, Category: {category.name}")

        mpesa = MpesaService()
        response = mpesa.initiate_stk_push(
            phone=phone,
            user=request.user if request.user.is_authenticated else None,
            amount=float(total_amount), # Send the DISCOUNTED amount
            event_id=event.id,
            ticket_category_id=category.id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=phone,
            quantity=quantity,
            callback_url=callback_url
        )

        if response.get('success'):
            return JsonResponse({
                'success': True,
                'message': response.get('customer_message', 'Check your phone for M-Pesa prompt'),
                'transaction_id': response.get('transaction_id'),
                'checkout_request_id': response.get('checkout_request_id')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': response.get('error', 'Payment initiation failed')
            })

    except Exception as e:
        logger.error(f"[STK] Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        })
        
# ═══════════════════════════════════════════════════════════════════════════════
# M-PESA CALLBACK
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def mpesa_callback(request):
    """
    Handle M-Pesa callback from Safaricom.
    ALWAYS returns 200 — errors cause retries and duplicate tickets.
    
    URL: /payments/mpesa-callback/
    """
    if request.method != 'POST':
        return HttpResponse(status=200)

    try:
        raw_body = request.body.decode('utf-8')
        logger.info(f"[CALLBACK] Received: {raw_body[:500]}")
        print(f"[CALLBACK] Received from Safaricom")

        callback_data = json.loads(raw_body)
        mpesa = MpesaService()
        success = mpesa.process_callback(callback_data)

        if success:
            print("[CALLBACK] ✅ Success")
        else:
            print("[CALLBACK] ⚠️ Non-success")

    except json.JSONDecodeError as e:
        logger.error(f"[CALLBACK] Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"[CALLBACK] Error: {e}", exc_info=True)

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK TEST
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def mpesa_callback_test(request):
    """
    Test endpoint — verify callback URL is reachable.
    
    URL: /payments/mpesa-callback-test/
    Usage: curl -X POST https://www.zozaprime.com/payments/mpesa-callback-test/
    """
    return JsonResponse({'status': 'ok', 'message': 'Callback reachable'})


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK PAYMENT STATUS — with time-guarded STK query fallback
#
# THE FIX: Don't query Safaricom until at least 15 seconds have passed
# since the STK push was sent. Before that, the fan hasn't even seen the
# prompt on their phone yet, and Safaricom returns ambiguous ResultCode 1
# which was being misinterpreted as "failed".
#
# FLOW:
# 0-15 seconds:  Return "pending" from DB only (no Safaricom query)
# 15+ seconds:   Query Safaricom directly if still pending
# ═══════════════════════════════════════════════════════════════════════════════

# Minimum seconds to wait before querying Safaricom
STK_QUERY_DELAY_SECONDS = 15

def check_payment_status(request, transaction_id):
    """
    Check payment status — frontend polls this every 3 seconds.
    
    URL: /payments/check-payment-status/<transaction_id>/
    """
    try:
        txn = Transaction.objects.filter(transaction_id=transaction_id).first()

        if not txn:
            return JsonResponse({'success': True, 'status': 'pending'})

        # ── Already resolved? Return immediately ──
        if txn.status in ('success', 'failed', 'cancelled'):
            return JsonResponse({
                'success': True,
                'status': txn.status,
                'transaction_id': txn.transaction_id,
                'receipt_number': txn.receipt_number,
                'amount': float(txn.amount),
            })

        # ── Still pending ──
        if txn.checkout_request_id:
            # Check if enough time has passed to query Safaricom
            elapsed = (timezone.now() - txn.timestamp).total_seconds()

            if elapsed < STK_QUERY_DELAY_SECONDS:
                # Too early — fan is still entering PIN
                # Just return pending, don't query Safaricom yet
                logger.info(
                    f"[STATUS] {transaction_id}: {elapsed:.0f}s elapsed, "
                    f"waiting {STK_QUERY_DELAY_SECONDS}s before query"
                )
                return JsonResponse({
                    'success': True,
                    'status': 'pending',
                    'transaction_id': txn.transaction_id,
                    'amount': float(txn.amount),
                })

            # Enough time passed — query Safaricom
            logger.info(f"[STATUS] {transaction_id}: {elapsed:.0f}s elapsed, querying Safaricom")
            print(f"[STATUS] Querying Safaricom for {transaction_id} ({elapsed:.0f}s elapsed)")

            mpesa = MpesaService()
            result = mpesa.query_stk_status(txn.checkout_request_id)

            print(f"[STATUS] Query result: {result['status']}")

            if result['status'] == 'success':
                txn.status = 'success'
                txn.save()
                mpesa._create_ticket_from_txn(txn)

                return JsonResponse({
                    'success': True,
                    'status': 'success',
                    'transaction_id': txn.transaction_id,
                    'receipt_number': txn.receipt_number,
                    'amount': float(txn.amount),
                })

            elif result['status'] == 'cancelled':
                txn.status = 'cancelled'
                txn.description = result.get('description', 'Cancelled by user')
                txn.save()
                return JsonResponse({'success': True, 'status': 'cancelled'})

            elif result['status'] == 'failed':
                txn.status = 'failed'
                txn.description = result.get('description', 'Payment failed')
                txn.save()
                return JsonResponse({'success': True, 'status': 'failed'})

            # result['status'] == 'pending' — still waiting
            # Fall through to return pending below

        # Still pending
        return JsonResponse({
            'success': True,
            'status': 'pending',
            'transaction_id': txn.transaction_id,
            'amount': float(txn.amount),
        })

    except Exception as e:
        logger.error(f"[STATUS] Error: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET CONFIRMATION PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def ticket_confirmation(request, transaction_id):
    """
    Display ticket confirmation with QR code.
    
    URL: /payments/ticket-confirmation/<transaction_id>/
    
    5-layer ticket lookup — never 404s:
    1. By M-Pesa receipt number
    2. By TXN_ code
    3. By QUERY_ code (legacy)
    4. By buyer details
    5. Create on the spot
    """
    try:
        txn = Transaction.objects.filter(transaction_id=transaction_id).first()

        if not txn:
            messages.error(request, 'Transaction not found.')
            return redirect('home')

        if txn.status != 'success':
            messages.error(request, 'Payment has not been completed.')
            return redirect('home')

        # ── Find the ticket ──
        ticket = None

        # Layer 1: By receipt number
        if txn.receipt_number:
            ticket = Ticket.objects.filter(
                transaction_code=txn.receipt_number
            ).first()

        # Layer 2: By TXN_ code
        if not ticket:
            ticket = Ticket.objects.filter(
                transaction_code=f"TXN_{txn.transaction_id}"
            ).first()

        # Layer 3: By QUERY_ code (from older version)
        if not ticket:
            ticket = Ticket.objects.filter(
                transaction_code=f"QUERY_{txn.transaction_id}"
            ).first()

        # Layer 4: By buyer details
        if not ticket:
            ticket = Ticket.objects.filter(
                event=txn.event,
                buyer_email=txn.buyer_email,
                ticket_category=txn.ticket_category,
            ).order_by('-purchased_at').first()

        # Layer 5: Create it now
        if not ticket:
            logger.warning(f"[CONFIRM] No ticket for {transaction_id}, creating")
            mpesa = MpesaService()
            ticket = mpesa._create_ticket_from_txn(txn)

        if not ticket:
            messages.error(request, 'Could not locate your ticket. Contact support.')
            return redirect('home')

        # ── Generate QR code ──
        qr_data_uri = ""
        try:
            from events.ticket_service import get_ticket_qr_base64
            qr_data_uri = get_ticket_qr_base64(ticket)
        except Exception as e:
            logger.error(f"[CONFIRM] QR failed: {e}")

        context = {
            'ticket': ticket,
            'transaction': txn,
            'event': txn.event,
            'ticket_category': txn.ticket_category,
            'qr_code': qr_data_uri,
        }

        return render(request, 'events/ticket_confirmation.html', context)

    except Exception as e:
        logger.error(f"[CONFIRM] Error: {e}", exc_info=True)
        messages.error(request, 'Error loading ticket confirmation.')
        return redirect('home')


# ═══════════════════════════════════════════════════════════════════════════════
# PAYSTACK PAYMENT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════


@login_required
def initiate_paystack_payment(request, slug):
    """
    Initiate Paystack checkout for ticket purchase.
    
    URL: /payments/initiate-paystack-payment/<slug>/
    """
    try:
        event = get_object_or_404(Event, slug=slug)

        buyer_name = request.POST.get('buyer_name', '').strip()
        buyer_email = request.POST.get('buyer_email', '').strip()
        buyer_phone = request.POST.get('buyer_phone', '').strip()
        category_id = request.POST.get('category_id')
        quantity = int(request.POST.get('quantity', 1))

        if not all([buyer_name, buyer_email, category_id]):
            return JsonResponse({'success': False, 'error': 'All fields are required'})

        category = get_object_or_404(TicketCategory, id=category_id, event=event)

        if category.is_free:
            return JsonResponse({
                'success': False,
                'error': 'This is a free ticket. Please use the RSVP flow.'
            }, status=400)

        if category.available_tickets < quantity:
            return JsonResponse({
                'success': False,
                'error': f'Only {category.available_tickets} tickets available'
            })

        # Base calculation
        unit_price = Decimal(str(category.effective_price))
        total_amount = unit_price * quantity

        # Apply promo code if provided
        promo_code_str = request.POST.get('promo_code_used') or request.session.get('promo_code')
        if promo_code_str:
            try:
                promo = PromoCode.objects.get(code=promo_code_str.upper().strip(), is_active=True)
                is_valid, _ = promo.validate(event=event)
                
                if is_valid:
                    if promo.discount_type == 'percentage':
                        discount = (promo.discount_value / Decimal('100')) * total_amount
                    else:
                        discount = promo.discount_value
                    
                    total_amount = max(total_amount - discount, Decimal('0'))
                    logger.info(f"[PAYSTACK] Promo Applied: {promo_code_str}. New Total: {total_amount}")
            except PromoCode.DoesNotExist:
                logger.warning(f"[PAYSTACK] Attempted invalid promo: {promo_code_str}")

        # Generate unique reference
        purchase_id = f"purchase_{uuid.uuid4()}"

        # Create callback URL
        payment_success_url = reverse('payments:paystack_payment_success', kwargs={'slug': slug})
        callback_url = f"{request.scheme}://{request.get_host()}{payment_success_url}"

        # Create checkout payload
        checkout_data = {
            "email": buyer_email,
            "amount": int(total_amount * 100),  # Convert to kobo (smallest currency unit)
            "currency": "NGN",
            "channels": ["card", "bank_transfer", "bank", "ussd", "qr", "mobile_money"],
            "reference": purchase_id,
            "callback_url": callback_url,
            "metadata": {
                "event_id": event.id,
                "category_id": category_id,
                "user_id": request.user.id if request.user.is_authenticated else None,
                "purchase_id": purchase_id,
                "buyer_name": buyer_name,
                "buyer_email": buyer_email,
                "buyer_phone": buyer_phone,
                "quantity": quantity,
            },
            "label": f"Checkout For {event.title} - {category.name}"
        }

        # Initiate checkout
        status, check_out_session_url_or_error_message = checkout(checkout_data)

        if status:
            # Create pending transaction
            transaction = Transaction.objects.create(
                transaction_id=purchase_id,
                user=request.user if request.user.is_authenticated else None,
                phone_number=buyer_phone,
                amount=total_amount,
                payment_method='paystack',
                event=event,
                ticket_category=category,
                buyer_name=buyer_name,
                buyer_email=buyer_email,
                buyer_phone=buyer_phone,
                quantity=quantity,
                status='pending',
                description=f'Paystack payment for {category.name} ticket'
            )

            return JsonResponse({
                'success': True,
                'authorization_url': check_out_session_url_or_error_message,
                'transaction_id': transaction.transaction_id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': check_out_session_url_or_error_message
            })

    except Exception as e:
        logger.error(f"[PAYSTACK] Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        })


def paystack_payment_success(request, slug):
    """
    Handle Paystack payment success callback.
    
    URL: /payments/paystack-payment-success/<slug>/
    """
    try:
        event = get_object_or_404(Event, slug=slug)
        reference = request.GET.get('reference')

        if not reference:
            messages.error(request, 'No payment reference provided.')
            return redirect('events:event_detail', slug=slug)

        transaction = Transaction.objects.filter(transaction_id=reference).first()

        if not transaction:
            messages.error(request, 'Transaction not found.')
            return redirect('events:event_detail', slug=slug)

        # Redirect to ticket confirmation
        return redirect('payments:ticket_confirmation', transaction_id=transaction.transaction_id)

    except Exception as e:
        logger.error(f"[PAYSTACK] Success callback error: {str(e)}", exc_info=True)
        messages.error(request, 'Error processing payment confirmation.')
        return redirect('events:event_detail', slug=slug)


@csrf_exempt
def paystack_webhook(request):
    """
    Handle Paystack webhook for payment verification.
    
    URL: /payments/paystack-webhook/
    """
    if request.method != 'POST':
        return HttpResponse(status=200)

    try:
        secret = settings.PAYSTACK_SECRET_KEY
        request_body = request.body

        # Generate hash to verify webhook is from Paystack
        import hmac
        import hashlib
        hash = hmac.new(secret.encode('utf-8'), request_body, hashlib.sha512).hexdigest()
        
        if hash == request.META.get('HTTP_X_PAYSTACK_SIGNATURE'):
            webhook_post_data = json.loads(request_body)
            logger.info(f"[PAYSTACK WEBHOOK] Received: {webhook_post_data}")

            if webhook_post_data["event"] == "charge.success":
                metadata = webhook_post_data["data"]["metadata"]
                
                event_id = metadata.get("event_id")
                category_id = metadata.get("category_id")
                user_id = metadata.get("user_id")
                purchase_id = metadata.get("purchase_id")
                buyer_name = metadata.get("buyer_name")
                buyer_email = metadata.get("buyer_email")
                buyer_phone = metadata.get("buyer_phone")
                quantity = metadata.get("quantity", 1)

                # Update transaction
                transaction = Transaction.objects.filter(transaction_id=purchase_id).first()
                if transaction:
                    transaction.status = 'success'
                    transaction.receipt_number = webhook_post_data["data"]["reference"]
                    transaction.transaction_date = timezone.now()
                    transaction.save()

                    # Create ticket
                    from events.ticket_service import create_ticket
                    try:
                        event = Event.objects.get(id=event_id)
                        category = TicketCategory.objects.get(id=category_id)
                        
                        for _ in range(quantity):
                            create_ticket(
                                event=event,
                                category=category,
                                buyer_name=buyer_name,
                                buyer_email=buyer_email,
                                buyer_phone=buyer_phone,
                                transaction_code=transaction.transaction_id,
                                payment_method='paystack'
                            )
                        
                        logger.info(f"[PAYSTACK WEBHOOK] Ticket created for {purchase_id}")
                    except Exception as e:
                        logger.error(f"[PAYSTACK WEBHOOK] Error creating ticket: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"[PAYSTACK WEBHOOK] Error: {str(e)}", exc_info=True)

    return HttpResponse(status=200)


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def payment_success(request):
    """Legacy Stripe handler."""
    return JsonResponse({'success': False, 'error': 'Please use M-Pesa payment'})