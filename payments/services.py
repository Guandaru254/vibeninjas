import base64
import requests
from datetime import datetime
from django.conf import settings
from .models import Transaction
from events.models import Ticket
from events.models import Event, TicketCategory
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class MpesaService:
    def __init__(self):
        self.base_url = settings.MPESA_BASE_URL
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY

    def generate_access_token(self):
        auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(auth_url, auth=(self.consumer_key, self.consumer_secret))
        return response.json().get('access_token')

    def generate_password(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        return base64.b64encode(data_to_encode.encode()).decode(), timestamp

    def initiate_stk_push(self, phone,user, amount, event_id, ticket_category_id, buyer_name, buyer_email, buyer_phone, quantity, callback_url):
        """Initiate STK push and create transaction record"""
        access_token = self.generate_access_token()
        password, timestamp = self.generate_password()

        # Get event and ticket category
        event = Event.objects.get(id=event_id)
        ticket_category = TicketCategory.objects.get(id=ticket_category_id)

        # Create transaction record
        transaction = Transaction.objects.create(
            phone_number=phone,
            amount=amount,
            user=user,
            event=event,
            ticket_category=ticket_category,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            buyer_phone=buyer_phone,
            quantity=quantity,
            payment_method='mpesa',
            status='pending'
        )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            # "Amount": str(int(amount)),
            "Amount": '1',
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": f"Ticket_{transaction.transaction_id}",
            "TransactionDesc": f"Payment for {event.title} - {ticket_category.name}"
        }

        print(f"STK Push payload: {payload}")

        response = requests.post(
            f'{self.base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers
        )

        response_data = response.json()
        print(f"STK Push response: {response_data}")

        if response_data.get('ResponseCode') == '0':
            # Update transaction with M-Pesa response data
            transaction.checkout_request_id = response_data.get('CheckoutRequestID')
            # transaction.merchant_request_id = response_data.get('MerchantRequestID')
            transaction.save()

        return {
            'success': response_data.get('ResponseCode') == '0',
            'transaction_id': transaction.transaction_id,
            'checkout_request_id': response_data.get('CheckoutRequestID'),
            'merchant_request_id': response_data.get('MerchantRequestID'),
            'response_description': response_data.get('ResponseDescription'),
            'customer_message': response_data.get('CustomerMessage')
        }

    def process_callback(self, callback_data):
        """Process the callback data from M-Pesa"""
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_desc = stk_callback.get('ResultDesc', '')
        
        transaction = Transaction.objects.filter(checkout_request_id=checkout_request_id).first()
        if not transaction:
            print(f"Transaction not found for checkout_request_id: {checkout_request_id}")
            return False
        
        if result_code == 0:
            # Payment successful
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            receipt_number = next((item['Value'] for item in callback_metadata if item['Name'] == 'MpesaReceiptNumber'), None)
            
            transaction.status = "success"
            transaction.receipt_number = receipt_number
            transaction.transaction_date = datetime.now()
            transaction.save()
            
            # Create ticket
            ticket = Ticket.objects.create(
                event=transaction.event,
                ticket_category=transaction.ticket_category,
                buyer_name=transaction.buyer_name,
                buyer_email=transaction.buyer_email,
                buyer_phone=transaction.buyer_phone,
                quantity=transaction.quantity,
                unit_price=transaction.ticket_category.price,
                total_amount=transaction.amount,
                transaction_code=transaction.receipt_number
            )
            
            # Update available tickets
            transaction.ticket_category.available_tickets -= transaction.quantity
            transaction.ticket_category.save()
            
            transaction.event.available_tickets -= transaction.quantity
            transaction.event.save()
            
            print(f"Transaction successful: {receipt_number}")
            
            # Send ticket email
            # self.send_ticket_email(ticket)
            
            return True
            
        elif result_code == 1:
            transaction.status = "failed"
            transaction.description = result_desc or "Payment failed due to an error."
            transaction.save()
            print(f"Transaction failed: {result_desc or 'No description provided.'}")
            
        elif result_code == 1032:  
            transaction.status = "cancelled"
            transaction.description = result_desc or "Transaction was cancelled by the user."
            transaction.save()
            print(f"Transaction cancelled: {result_desc or 'No description provided.'}")
        
        elif result_code == 2001:
            transaction.status = "failed"
            transaction.description = result_desc or "Payment failed due to incorrect details."
            transaction.save()
            print(f"Transaction failed: {result_desc or 'No description provided.'}")
            
            
        else:
            transaction.status = "unknown"
            transaction.description = f"Unhandled result code: {result_code}. {result_desc}"
            transaction.save()
            print(f"Unknown transaction status: {result_desc}")
            
        return False

    def send_ticket_email(self, ticket):
        """Send ticket confirmation email"""
        try:
            subject = f"Ticket Confirmation - {ticket.event.title}"
            context = {
                'ticket': ticket,
                'event': ticket.event,
                'ticket_category': ticket.ticket_category,
            }
            
            html_content = render_to_string('emails/ticket_confirmation.html', context)
            text_content = render_to_string('emails/ticket_confirmation.txt', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[ticket.buyer_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            print(f"Ticket confirmation email sent to {ticket.buyer_email}")
            
        except Exception as e:
            print(f"Failed to send ticket email: {str(e)}")

    def check_transaction_status(self, transaction_id):
        """Check the status of a transaction"""
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            return {
                'status': transaction.status,
                'receipt_number': transaction.receipt_number,
                'transaction_id': transaction.transaction_id,
                'amount': transaction.amount
            }
        except Transaction.DoesNotExist:
            return None