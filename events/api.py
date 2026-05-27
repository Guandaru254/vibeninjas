"""
Gate Verification API Endpoints
================================
API endpoints for gate entry verification.

Location: events/api.py
URL Pattern: POST /api/v1/gate/verify-ticket/
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .gate_verification_utils import (
    validate_hmac_signature,
    verify_ticket,
    mark_ticket_as_used,
)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def verify_ticket_gate(request):
    """
    Verify a ticket at the gate using HMAC signature.
    
    Endpoint: POST /api/v1/gate/verify-ticket/
    
    Request payload:
    {
        "ticket_code": "ABC12345",
        "timestamp": "2026-05-27T14:30:00Z",
        "signature": "abc123def456..."
    }
    
    Response (200 OK - Valid Ticket):
    {
        "success": true,
        "message": "Ticket verified successfully",
        "ticket": {
            "ticket_code": "ABC12345",
            "status": "valid",
            "buyer_name": "John Doe",
            "buyer_email": "john@example.com",
            "event_title": "Tech Conference 2026",
            "event_date": "2026-05-27T18:00:00Z",
            "event_location": "Convention Center",
            "ticket_category": "VIP",
            "quantity": 1,
            "verified_at": "2026-05-27T14:30:15Z"
        }
    }
    
    Response (400 Bad Request - Invalid Request):
    {
        "success": false,
        "error": "Missing required field: ticket_code"
    }
    
    Response (401 Unauthorized - Invalid Signature):
    {
        "success": false,
        "error": "Invalid signature"
    }
    
    Response (404 Not Found):
    {
        "success": false,
        "error": "Ticket not found"
    }
    
    Response (409 Conflict - Ticket Already Used):
    {
        "success": false,
        "error": "Ticket already used at 2026-05-27T14:25:00Z"
    }
    """
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON payload'
            }, status=400)
        
        # Extract required fields
        ticket_code = data.get('ticket_code', '').strip()
        timestamp = data.get('timestamp', '').strip()
        signature = data.get('signature', '').strip()
        
        # Validate required fields
        missing_fields = []
        if not ticket_code:
            missing_fields.append('ticket_code')
        if not timestamp:
            missing_fields.append('timestamp')
        if not signature:
            missing_fields.append('signature')
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Validate HMAC signature
        is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, signature)
        if not is_valid:
            logger.warning(f"Invalid signature for ticket {ticket_code}: {error_msg}")
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=401)
        
        # Verify ticket exists and is in valid state
        ticket_data, error_msg = verify_ticket(ticket_code)
        if error_msg:
            if "not found" in error_msg.lower():
                status_code = 404
            elif "already used" in error_msg.lower():
                status_code = 409
            else:
                status_code = 400
            
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=status_code)
        
        # Mark ticket as used
        success, mark_msg = mark_ticket_as_used(ticket_code)
        if not success:
            logger.error(f"Failed to mark ticket as used: {mark_msg}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to process ticket: {mark_msg}'
            }, status=500)
        
        # Return success with ticket details
        return JsonResponse({
            'success': True,
            'message': 'Ticket verified and marked as used',
            'ticket': ticket_data
        }, status=200)
    
    except Exception as e:
        logger.error(f"Error in verify_ticket_gate: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_POST
def validate_gate_signature(request):
    """
    Validate a gate verification signature WITHOUT marking ticket as used.
    
    Use this for pre-validation or testing purposes.
    
    Endpoint: POST /api/v1/gate/validate-signature/
    
    Request payload:
    {
        "ticket_code": "ABC12345",
        "timestamp": "2026-05-27T14:30:00Z",
        "signature": "abc123def456..."
    }
    
    Response (200 OK - Valid Signature):
    {
        "success": true,
        "message": "Signature is valid"
    }
    
    Response (401 Unauthorized):
    {
        "success": false,
        "error": "Invalid signature"
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    
    ticket_code = data.get('ticket_code', '').strip()
    timestamp = data.get('timestamp', '').strip()
    signature = data.get('signature', '').strip()
    
    if not all([ticket_code, timestamp, signature]):
        return JsonResponse({
            'success': False,
            'error': 'Missing required fields'
        }, status=400)
    
    is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, signature)
    
    if is_valid:
        return JsonResponse({
            'success': True,
            'message': 'Signature is valid'
        }, status=200)
    else:
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=401)
