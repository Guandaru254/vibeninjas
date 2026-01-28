from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from events.models import Event, TicketCategory, Ticket
from .models import Transaction
from events.forms import TicketPurchaseForm
from .services import MpesaService
import json


def checkout(request, pk):
    event = get_object_or_404(Event, pk=pk)
    category_id = request.GET.get('category')
    
    if not category_id:
        messages.error(request, 'Please select a ticket category.')
        return redirect('event_detail', pk=event.pk)
    
    try:
        selected_category = TicketCategory.objects.get(
            id=category_id,
            # event=event,
            available_tickets__gt=0
        )
    except TicketCategory.DoesNotExist:
        messages.error(request, 'Selected ticket category is not available.')
        return redirect('event_detail', pk=event.pk)
    
    initial_data = {
        'ticket_category': selected_category,
        'quantity': 1
    }
    
    if request.user.is_authenticated:
        initial_data.update({
            'buyer_name': request.user.get_full_name(),
            'buyer_email': request.user.email
        })
    
    form = TicketPurchaseForm(
        selected_category.event, 
        initial=initial_data
    )
    
    context = {
        'event': selected_category.event,
        'selected_category': selected_category,
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    
    return render(request, 'events/checkout.html', context)


@require_POST
def initiate_mpesa_payment(request, pk):
    """Initiate M-Pesa STK push payment"""
    try:
        event = get_object_or_404(Event, pk=pk)
        
        # Get form data
        buyer_name = request.POST.get('buyer_name')
        buyer_email = request.POST.get('buyer_email')
        buyer_phone = request.POST.get('buyer_phone')
        quantity = int(request.POST.get('quantity', 1))
        category_id = request.POST.get('category_id')
        
        # Get ticket category
        ticket_category = get_object_or_404(TicketCategory, id=category_id, event=event)
        
        if ticket_category.available_tickets < quantity:
            return JsonResponse({
                'success': False,
                'error': 'Not enough tickets available for the selected category.'
            })
        
        # Calculate total amount
        total_amount = ticket_category.price * quantity
        
        # Validate phone number (ensure it's in correct format)
        if not buyer_phone or len(buyer_phone) < 10:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a valid phone number for M-Pesa payment'
            })
        
        # Format phone number (assuming Kenyan format)
        if buyer_phone.startswith('0'):
            buyer_phone = '254' + buyer_phone[1:]
        elif buyer_phone.startswith('+254'):
            buyer_phone = buyer_phone[1:]
        elif not buyer_phone.startswith('254'):
            buyer_phone = '254' + buyer_phone
        
        # Create callback URL
        # callback_url = request.build_absolute_uri(reverse('mpesa_callback'))
        # if not callback_url.endswith('/'):
        #     callback_url += '/'
            
        callback_url = f"{settings.MPESA_CALLBACK_URL}/mpesa-callback/"
        
        print(f"Callback URL: {callback_url}")
        
        # Initialize M-Pesa service
        mpesa_service = MpesaService()
        
        # Initiate STK push
        result = mpesa_service.initiate_stk_push(
            phone=buyer_phone,
            user=request.user if request.user.is_authenticated else None,
            amount=total_amount,
            event_id=event.id,
            ticket_category_id=ticket_category.id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=buyer_phone,
            quantity=quantity,
            callback_url=callback_url
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'transaction_id': result['transaction_id'],
                'message': result['customer_message'],
                'checkout_request_id': result['checkout_request_id']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['response_description']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Handle M-Pesa callback"""
    try:
        callback_data = json.loads(request.body)
        print(f"M-Pesa callback received: {callback_data}")
        
        mpesa_service = MpesaService()
        success = mpesa_service.process_callback(callback_data)
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Callback processed successfully'
        })
        
    except Exception as e:
        print(f"Error processing M-Pesa callback: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': f'Error processing callback: {str(e)}'
        })


def check_payment_status(request, transaction_id):
    """Check payment status"""
    try:
        mpesa_service = MpesaService()
        status = mpesa_service.check_transaction_status(transaction_id)
        
        if status:
            return JsonResponse({
                'success': True,
                'status': status['status'],
                'receipt_number': status['receipt_number'],
                'amount': status['amount']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Transaction not found'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def ticket_confirmation(request, transaction_id):
    """Display ticket confirmation page"""
    try:
        transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
        tickets = get_object_or_404(Ticket, transaction_code=transaction.receipt_number)
        
        context = {
            'transaction': transaction,
            'ticket': tickets,
            'event': transaction.event,
            'ticket_category': transaction.ticket_category,
        }
        
        return render(request, 'events/ticket_confirmation.html', context)
        
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('home')


@require_POST
def payment_success(request):
    """Handle Stripe payment success (keeping for backward compatibility)"""
    try:
        payload = json.loads(request.body)
        payment_intent_id = payload.get('payment_intent_id')
        
        # Handle Stripe payment success logic here
        # This can coexist with M-Pesa payments
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})