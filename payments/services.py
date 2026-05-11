"""
ZOZAPRIME M-Pesa Payment Service
=================================
Location: payments/services.py (REPLACE existing file)
"""
import base64
import logging
import requests
from datetime import datetime

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Transaction
from events.models import Ticket, Event, TicketCategory

logger = logging.getLogger(__name__)


class MpesaService:
    """M-Pesa payment service — STK push, callbacks, and status queries."""

    def __init__(self):
        self.base_url = settings.MPESA_BASE_URL
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY

    # ═══════════════════════════════════════════════════════════════════════
    # AUTH
    # ═══════════════════════════════════════════════════════════════════════

    def generate_access_token(self):
        """Generate OAuth access token from Safaricom API."""
        try:
            url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            response.raise_for_status()
            token = response.json().get('access_token')
            if not token:
                raise Exception("No access_token in Safaricom response")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"[AUTH] Token generation failed: {str(e)}")
            raise Exception("Failed to connect to M-Pesa. Please try again.")

    def generate_password(self):
        """Generate Base64-encoded password and timestamp for STK push."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        password = base64.b64encode(data_to_encode.encode()).decode()
        return password, timestamp

    # ═══════════════════════════════════════════════════════════════════════
    # STK PUSH
    # ═══════════════════════════════════════════════════════════════════════

    def initiate_stk_push(self, phone, user, amount, event_id, ticket_category_id,
                          buyer_name, buyer_email, buyer_phone, quantity, callback_url):
        """Initiate M-Pesa STK Push payment."""
        try:
            event = Event.objects.get(id=event_id)
            category = TicketCategory.objects.get(id=ticket_category_id)

            if category.available_tickets < quantity:
                return {
                    'success': False,
                    'error': f'Only {category.available_tickets} tickets available'
                }

            transaction = Transaction.objects.create(
                phone_number=phone,
                amount=amount,
                user=user if user and user.is_authenticated else None,
                event=event,
                ticket_category=category,
                buyer_name=buyer_name,
                buyer_email=buyer_email,
                buyer_phone=buyer_phone,
                quantity=quantity,
                payment_method='mpesa',
                status='pending'
            )

            logger.info(f"[STK] Created transaction: {transaction.transaction_id}")
            print(f"[STK] Created: {transaction.transaction_id}")

            access_token = self.generate_access_token()
            password, timestamp = self.generate_password()

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # ┌─────────────────────────────────────────────────────────┐
            # │ PRODUCTION TOGGLE                                       │
            # │ TESTING:    stk_amount = "1"                            │
            # │ PRODUCTION: stk_amount = str(int(amount))               │
            # └─────────────────────────────────────────────────────────┘
            stk_amount = str(int(amount))  

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": stk_amount,
                "PartyA": phone,
                "PartyB": self.shortcode,
                "PhoneNumber": phone,
                "CallBackURL": callback_url,
                "AccountReference": f"ZP_{transaction.transaction_id}",
                "TransactionDesc": f"{event.title} - {category.name}"
            }

            logger.info(f"[STK] Sending: phone={phone}, amount={stk_amount}")
            print(f"[STK] Phone: {phone}, Amount: {stk_amount}")

            response = requests.post(
                f'{self.base_url}/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers=headers,
                timeout=30
            )

            data = response.json()
            logger.info(f"[STK] Response: {data}")
            print(f"[STK] Response: {data}")

            if data.get('ResponseCode') == '0':
                transaction.checkout_request_id = data.get('CheckoutRequestID')
                transaction.save(update_fields=['checkout_request_id'])

                print(f"[STK] ✅ Initiated: {transaction.transaction_id}")

                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'customer_message': data.get(
                        'CustomerMessage',
                        'Check your phone for M-Pesa prompt'
                    ),
                }
            else:
                transaction.status = 'failed'
                transaction.description = data.get('ResponseDescription', 'STK push failed')
                transaction.save(update_fields=['status', 'description'])

                print(f"[STK] ❌ Failed: {data.get('ResponseDescription')}")

                return {
                    'success': False,
                    'error': data.get(
                        'CustomerMessage',
                        'Payment request failed. Please try again.'
                    )
                }

        except Event.DoesNotExist:
            return {'success': False, 'error': 'Event not found'}
        except TicketCategory.DoesNotExist:
            return {'success': False, 'error': 'Ticket category not found'}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout. Please try again.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"[STK] Request error: {str(e)}")
            return {'success': False, 'error': 'Connection error. Please try again.'}
        except Exception as e:
            logger.error(f"[STK] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'An error occurred. Please try again.'}

    # ═══════════════════════════════════════════════════════════════════════
    # CALLBACK PROCESSING
    # ═══════════════════════════════════════════════════════════════════════

    def process_callback(self, callback_data):
        """Process M-Pesa STK push callback from Safaricom."""
        try:
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_desc = stk_callback.get('ResultDesc', '')

            logger.info(f"[CALLBACK] checkout_id={checkout_request_id}, code={result_code}")
            print(f"[CALLBACK] code={result_code}, desc={result_desc}")

            transaction = Transaction.objects.filter(
                checkout_request_id=checkout_request_id
            ).first()

            if not transaction:
                logger.error(f"[CALLBACK] No transaction for {checkout_request_id}")
                return False

            # Prevent double-processing
            if transaction.status == 'success':
                logger.info(f"[CALLBACK] Already succeeded: {transaction.transaction_id}")
                return True

            if result_code == 0:
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = next(
                    (item['Value'] for item in callback_metadata
                     if item['Name'] == 'MpesaReceiptNumber'),
                    None
                )
                paid_amount = next(
                    (item['Value'] for item in callback_metadata
                     if item['Name'] == 'Amount'),
                    None
                )

                transaction.status = 'success'
                transaction.receipt_number = receipt_number
                transaction.transaction_date = datetime.now()
                transaction.save()

                logger.info(f"[CALLBACK] ✅ Receipt: {receipt_number}, Paid: {paid_amount}")
                print(f"[CALLBACK] ✅ Receipt: {receipt_number}")

                self._create_ticket_from_txn(transaction)
                return True

            elif result_code == 1032:
                transaction.status = 'cancelled'
                transaction.description = result_desc or 'Cancelled by user'
                transaction.save()
                print(f"[CALLBACK] Cancelled")

            elif result_code in (1, 2001):
                transaction.status = 'failed'
                transaction.description = result_desc or 'Payment failed'
                transaction.save()
                print(f"[CALLBACK] Failed ({result_code})")

            else:
                transaction.status = 'failed'
                transaction.description = f"{result_desc} (Code: {result_code})"
                transaction.save()
                print(f"[CALLBACK] Unknown code {result_code}")

            return False

        except Exception as e:
            logger.error(f"[CALLBACK] Error: {str(e)}", exc_info=True)
            print(f"[CALLBACK] ❌ Error: {str(e)}")
            return False

    # ═══════════════════════════════════════════════════════════════════════
    # STK STATUS QUERY — Fallback when callback doesn't arrive
    #
    # CRITICAL FIX: Safaricom returns ResultCode 1 with description
    # "The service request is processed successfully" when the transaction
    # is STILL IN PROGRESS. The word "processed" (past tense) was not
    # being caught by the old check for "processing" (present tense).
    #
    # We now treat ANY ResultCode 1 response as "pending" unless the
    # description explicitly says "failed", "rejected", "insufficient",
    # or "wrong pin". This prevents false "failed" statuses.
    # ═══════════════════════════════════════════════════════════════════════

    def query_stk_status(self, checkout_request_id):
        """
        Query Safaricom for STK push status.
        Used when callback hasn't arrived yet.
        """
        try:
            access_token = self.generate_access_token()
            password, timestamp = self.generate_password()

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            logger.info(f"[QUERY] Querying {checkout_request_id}")
            print(f"[QUERY] Querying {checkout_request_id}")

            response = requests.post(
                f'{self.base_url}/mpesa/stkpushquery/v1/query',
                json=payload,
                headers=headers,
                timeout=30
            )

            data = response.json()
            logger.info(f"[QUERY] Response: {data}")
            print(f"[QUERY] ResultCode={data.get('ResultCode')}, Desc={data.get('ResultDesc')}")

            # Normalize ResultCode to int
            result_code = data.get('ResultCode')
            if isinstance(result_code, str):
                try:
                    result_code = int(result_code)
                except (ValueError, TypeError):
                    result_code = -1

            result_desc = data.get('ResultDesc', '')
            desc_lower = result_desc.lower()

            # ── ResultCode 0 = Payment completed successfully ──
            if result_code == 0:
                print(f"[QUERY] ✅ Success")
                return {
                    'status': 'success',
                    'description': result_desc,
                    'data': data
                }

            # ── ResultCode 1032 = User cancelled ──
            elif result_code == 1032:
                print(f"[QUERY] Cancelled")
                return {
                    'status': 'cancelled',
                    'description': result_desc,
                    'data': data
                }

            # ── ResultCode 1 = AMBIGUOUS ──
            # Safaricom uses code 1 for BOTH "still processing" and "failed"
            # Their description "The service request is processed successfully"
            # actually means "we received your query successfully" NOT "payment succeeded"
            #
            # RULE: Treat code 1 as PENDING unless description contains
            # explicit failure words. This prevents false "failed" statuses.
            elif result_code == 1:
                # Check for explicit failure indicators
                failure_words = [
                    'insufficient', 'wrong pin', 'rejected', 'failed',
                    'not enough', 'locked', 'blocked', 'exceeded'
                ]
                is_definite_failure = any(word in desc_lower for word in failure_words)

                if is_definite_failure:
                    print(f"[QUERY] Failed (definite): {result_desc}")
                    return {
                        'status': 'failed',
                        'description': result_desc,
                        'data': data
                    }
                else:
                    # "processed successfully", "processing", or anything else
                    # = still in progress, fan hasn't entered PIN yet
                    print(f"[QUERY] Pending (code 1, not definite failure): {result_desc}")
                    return {
                        'status': 'pending',
                        'description': result_desc,
                        'data': data
                    }

            # ── ResultCode 2001 = Wrong PIN / Insufficient funds ──
            elif result_code == 2001:
                print(f"[QUERY] Failed (2001)")
                return {
                    'status': 'failed',
                    'description': result_desc,
                    'data': data
                }

            # ── Any other code ──
            else:
                print(f"[QUERY] Unknown code {result_code}")
                return {
                    'status': 'failed',
                    'description': result_desc,
                    'data': data
                }

        except requests.exceptions.Timeout:
            print("[QUERY] Timeout")
            return {'status': 'pending', 'error': 'Query timeout — will retry'}

        except requests.exceptions.RequestException as e:
            logger.error(f"[QUERY] Request error: {str(e)}")
            return {'status': 'pending', 'error': str(e)}

        except Exception as e:
            logger.error(f"[QUERY] Error: {str(e)}")
            return {'status': 'pending', 'error': str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # TICKET CREATION
    #
    # DUPLICATE FIX: Checks by transaction_code (unique per payment),
    # NOT by buyer email+phone (which blocked repeat purchases).
    # ═══════════════════════════════════════════════════════════════════════

    def _create_ticket_from_txn(self, txn):
        """Create ticket from successful transaction. Prevents duplicates."""
        tx_code = txn.receipt_number or f"TXN_{txn.transaction_id}"

        existing = Ticket.objects.filter(transaction_code=tx_code).first()
        if existing:
            logger.info(f"[TICKET] Already exists: {existing.id} for {tx_code}")
            print(f"[TICKET] Already exists: {existing.id}")
            return existing

        try:
            with db_transaction.atomic():
                ticket = Ticket.objects.create(
                    event=txn.event,
                    ticket_category=txn.ticket_category,
                    buyer_name=txn.buyer_name,
                    buyer_email=txn.buyer_email,
                    buyer_phone=txn.buyer_phone,
                    quantity=txn.quantity,
                    unit_price=txn.ticket_category.price,
                    total_amount=txn.amount,
                    transaction_code=tx_code,
                    status='confirmed',
                )

                category = TicketCategory.objects.select_for_update().get(
                    id=txn.ticket_category_id
                )
                category.available_tickets = max(0, category.available_tickets - txn.quantity)
                category.save(update_fields=['available_tickets'])

            logger.info(f"[TICKET] ✅ Created: {ticket.id}, code={ticket.ticket_code}")
            print(f"[TICKET] ✅ Created {ticket.id}")

            # Send email with QR (non-blocking)
            try:
                from events.ticket_service import send_ticket_email
                send_ticket_email(ticket)
            except Exception as e:
                logger.error(f"[TICKET] Email failed (non-fatal): {e}")
                print(f"[TICKET] ⚠️ Email failed: {e}")

            return ticket

        except Exception as e:
            logger.error(f"[TICKET] Creation failed: {e}", exc_info=True)
            print(f"[TICKET] ❌ Failed: {e}")
            return None

    def check_transaction_status(self, transaction_id):
        """Check transaction status from DB only."""
        try:
            txn = Transaction.objects.get(transaction_id=transaction_id)
            return {
                'status': txn.status,
                'receipt_number': txn.receipt_number,
                'transaction_id': txn.transaction_id,
                'amount': float(txn.amount),
            }
        except Transaction.DoesNotExist:
            return None