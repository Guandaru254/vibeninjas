"""
ZOZAPRIME Payment Views
========================
Location: payments/views.py (REPLACE existing file)
"""
import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import timedelta

from events.models import Event, TicketCategory, Ticket
from .models import Transaction
from .services import MpesaService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# INITIATE M-PESA STK PUSH
# ═══════════════════════════════════════════════════════════════════════════════
from decimal import Decimal
from events.models import PromoCode  # Ensure this import is correct

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
# LEGACY
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def payment_success(request):
    """Legacy Stripe handler."""
    return JsonResponse({'success': False, 'error': 'Please use M-Pesa payment'})