"""
Gate Verification Utilities
===========================
Handles HMAC signature validation and ticket verification logic for gate entry.

Location: events/gate_verification_utils.py
"""
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Ticket

logger = logging.getLogger(__name__)

# Default timestamp validity (5 minutes)
SIGNATURE_VALIDITY_SECONDS = getattr(settings, 'GATE_VERIFICATION_VALIDITY_SECONDS', 300)
SECRET_KEY = getattr(settings, 'GATE_VERIFICATION_SECRET_KEY', settings.SECRET_KEY)


def generate_hmac_signature(ticket_code: str, timestamp: str) -> str:
    """
    Generate HMAC-SHA256 signature for gate verification.
    
    Args:
        ticket_code: The ticket code to verify
        timestamp: ISO format timestamp (e.g., "2026-05-27T14:30:00Z")
    
    Returns:
        Hex-encoded HMAC-SHA256 signature
    
    Example:
        >>> sig = generate_hmac_signature("ABC12345", "2026-05-27T14:30:00Z")
        >>> len(sig)
        64
    """
    payload = f"{ticket_code}:{timestamp}".encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return signature


def validate_hmac_signature(ticket_code: str, timestamp: str, provided_signature: str) -> tuple[bool, str]:
    """
    Validate HMAC signature and timestamp.
    
    Args:
        ticket_code: The ticket code
        timestamp: ISO format timestamp string
        provided_signature: The signature to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        - (True, "") if valid
        - (False, error_msg) if invalid
    """
    try:
        # Parse timestamp
        try:
            request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid timestamp format. Use ISO format (e.g., 2026-05-27T14:30:00Z)"
        
        # Check timestamp validity (prevent replay attacks)
        now = timezone.now()
        if request_time.tzinfo is None:
            request_time = timezone.make_aware(request_time)
        
        time_diff = (now - request_time).total_seconds()
        
        if time_diff < 0:
            return False, "Timestamp is in the future"
        
        if time_diff > SIGNATURE_VALIDITY_SECONDS:
            return False, f"Request expired. Maximum age is {SIGNATURE_VALIDITY_SECONDS} seconds"
        
        # Validate HMAC signature
        expected_signature = generate_hmac_signature(ticket_code, timestamp)
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning(f"Invalid HMAC signature for ticket {ticket_code}")
            return False, "Invalid signature"
        
        return True, ""
    
    except Exception as e:
        logger.error(f"Error validating HMAC signature: {str(e)}")
        return False, f"Signature validation error: {str(e)}"


def verify_ticket(ticket_code: str) -> tuple[dict, str]:
    """
    Verify and retrieve ticket details.
    
    Args:
        ticket_code: The ticket code to verify
    
    Returns:
        Tuple of (ticket_data: dict, error_message: str)
        - ticket_data contains ticket details if found and valid
        - error_message if there's an error
    """
    try:
        ticket = Ticket.objects.select_related(
            'event', 'ticket_category', 'buyer'
        ).get(ticket_code=ticket_code)
    except Ticket.DoesNotExist:
        return {}, "Ticket not found"
    
    # Check ticket status
    if ticket.status == 'cancelled':
        return {}, "Ticket has been cancelled"
    
    if ticket.status == 'used':
        return {}, f"Ticket already used at {ticket.used_at.isoformat()}"
    
    if ticket.status == 'pending':
        return {}, "Ticket payment is still pending"
    
    # Check event date (gate should not open before event)
    now = timezone.now()
    event_date = ticket.event.date
    time_before_event = (event_date - now).total_seconds() / 3600  # hours
    
    if time_before_event > 1:
        return {}, f"Gate opens 1 hour before event (in {time_before_event:.1f} hours)"
    
    if time_before_event < -24:
        return {}, "Event has ended (closed over 24 hours ago)"
    
    # Build ticket data
    ticket_data = {
        'ticket_code': ticket.ticket_code,
        'status': 'valid',
        'buyer_name': ticket.buyer_name,
        'buyer_email': ticket.buyer_email,
        'event_title': ticket.event.title,
        'event_date': ticket.event.date.isoformat(),
        'event_location': ticket.event.location,
        'ticket_category': ticket.ticket_category.name if ticket.ticket_category else 'General',
        'quantity': ticket.quantity,
        'verified_at': now.isoformat(),
    }
    
    return ticket_data, ""


def mark_ticket_as_used(ticket_code: str) -> tuple[bool, str]:
    """
    Mark a ticket as used at the gate.
    
    Args:
        ticket_code: The ticket code
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        ticket = Ticket.objects.get(ticket_code=ticket_code)
        ticket.mark_as_used()
        logger.info(f"Ticket {ticket_code} marked as used at gate")
        return True, "Ticket marked as used"
    except Ticket.DoesNotExist:
        return False, "Ticket not found"
    except Exception as e:
        logger.error(f"Error marking ticket as used: {str(e)}")
        return False, f"Error marking ticket: {str(e)}"
