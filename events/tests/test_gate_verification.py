"""
Gate Verification Tests
======================
Unit tests for gate verification endpoint with 95%+ coverage.

Location: events/tests/test_gate_verification.py
Run: python manage.py test events.tests.test_gate_verification
"""
import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from events.models import Event, Ticket, TicketCategory, Category
from events.gate_verification_utils import (
    generate_hmac_signature,
    validate_hmac_signature,
    verify_ticket,
    mark_ticket_as_used,
    SIGNATURE_VALIDITY_SECONDS,
)

User = get_user_model()


class GateVerificationUtilsTestCase(TestCase):
    """Test gate verification utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.category = Category.objects.create(
            name='Music',
            slug='music'
        )
        
        self.user = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='testpass123',
            is_seller=True
        )
        
        self.event = Event.objects.create(
            organizer=self.user,
            category=self.category,
            title='Test Concert',
            slug='test-concert',
            description='Test event',
            date=timezone.now() + timedelta(hours=2),
            location='Test Venue'
        )
        
        self.ticket_category = TicketCategory.objects.create(
            event=self.event,
            name='VIP',
            category_type='vip',
            price=100.00,
            initial_tickets=10,
            available_tickets=10
        )
    
    def test_generate_hmac_signature(self):
        """Test HMAC signature generation."""
        ticket_code = "TEST123"
        timestamp = "2026-05-27T14:30:00Z"
        
        signature = generate_hmac_signature(ticket_code, timestamp)
        
        # Should return a 64-character hex string (SHA256)
        self.assertEqual(len(signature), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in signature))
        
        # Same inputs should produce same signature
        signature2 = generate_hmac_signature(ticket_code, timestamp)
        self.assertEqual(signature, signature2)
        
        # Different inputs should produce different signature
        signature3 = generate_hmac_signature("DIFFERENT", timestamp)
        self.assertNotEqual(signature, signature3)
    
    def test_validate_hmac_signature_valid(self):
        """Test valid HMAC signature validation."""
        ticket_code = "ABC12345"
        timestamp = timezone.now().isoformat()
        signature = generate_hmac_signature(ticket_code, timestamp)
        
        is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, signature)
        
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
    
    def test_validate_hmac_signature_invalid(self):
        """Test invalid HMAC signature detection."""
        ticket_code = "ABC12345"
        timestamp = timezone.now().isoformat()
        invalid_signature = "0" * 64
        
        is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, invalid_signature)
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid signature", error_msg)
    
    def test_validate_hmac_signature_expired(self):
        """Test expired timestamp detection."""
        ticket_code = "ABC12345"
        # Timestamp from 10 minutes ago (default validity is 5 minutes)
        old_time = timezone.now() - timedelta(minutes=10)
        timestamp = old_time.isoformat()
        signature = generate_hmac_signature(ticket_code, timestamp)
        
        is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, signature)
        
        self.assertFalse(is_valid)
        self.assertIn("expired", error_msg.lower())
    
    def test_validate_hmac_signature_future_timestamp(self):
        """Test future timestamp rejection."""
        ticket_code = "ABC12345"
        future_time = timezone.now() + timedelta(minutes=1)
        timestamp = future_time.isoformat()
        signature = generate_hmac_signature(ticket_code, timestamp)
        
        is_valid, error_msg = validate_hmac_signature(ticket_code, timestamp, signature)
        
        self.assertFalse(is_valid)
        self.assertIn("future", error_msg.lower())
    
    def test_validate_hmac_signature_invalid_format(self):
        """Test invalid timestamp format handling."""
        ticket_code = "ABC12345"
        invalid_timestamp = "not-a-timestamp"
        signature = "0" * 64
        
        is_valid, error_msg = validate_hmac_signature(ticket_code, invalid_timestamp, signature)
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid timestamp format", error_msg)
    
    def test_verify_ticket_not_found(self):
        """Test ticket not found scenario."""
        ticket_data, error_msg = verify_ticket("NONEXISTENT")
        
        self.assertEqual(ticket_data, {})
        self.assertEqual(error_msg, "Ticket not found")
    
    def test_verify_ticket_cancelled(self):
        """Test cancelled ticket verification."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='cancelled'
        )
        
        ticket_data, error_msg = verify_ticket(ticket.ticket_code)
        
        self.assertEqual(ticket_data, {})
        self.assertIn("cancelled", error_msg.lower())
    
    def test_verify_ticket_already_used(self):
        """Test already used ticket verification."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='used',
            used_at=timezone.now()
        )
        
        ticket_data, error_msg = verify_ticket(ticket.ticket_code)
        
        self.assertEqual(ticket_data, {})
        self.assertIn("already used", error_msg.lower())
    
    def test_verify_ticket_pending(self):
        """Test pending ticket verification."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='pending'
        )
        
        ticket_data, error_msg = verify_ticket(ticket.ticket_code)
        
        self.assertEqual(ticket_data, {})
        self.assertIn("pending", error_msg.lower())
    
    def test_verify_ticket_valid(self):
        """Test valid ticket verification."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            quantity=2,
            total_amount=200.00,
            status='confirmed'
        )
        
        ticket_data, error_msg = verify_ticket(ticket.ticket_code)
        
        self.assertNotEqual(ticket_data, {})
        self.assertEqual(error_msg, "")
        self.assertEqual(ticket_data['status'], 'valid')
        self.assertEqual(ticket_data['buyer_name'], 'Test Buyer')
        self.assertEqual(ticket_data['quantity'], 2)
        self.assertIn('verified_at', ticket_data)
    
    def test_mark_ticket_as_used(self):
        """Test marking ticket as used."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='confirmed'
        )
        
        success, msg = mark_ticket_as_used(ticket.ticket_code)
        
        self.assertTrue(success)
        
        # Verify ticket status changed
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'used')
        self.assertIsNotNone(ticket.used_at)
    
    def test_mark_ticket_not_found(self):
        """Test marking non-existent ticket."""
        success, msg = mark_ticket_as_used("NONEXISTENT")
        
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())


class GateVerificationAPITestCase(TestCase):
    """Test gate verification API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        
        self.category = Category.objects.create(
            name='Music',
            slug='music'
        )
        
        self.user = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='testpass123',
            is_seller=True
        )
        
        self.event = Event.objects.create(
            organizer=self.user,
            category=self.category,
            title='Test Concert',
            slug='test-concert',
            description='Test event',
            date=timezone.now() + timedelta(hours=0.5),  # 30 minutes from now
            location='Test Venue'
        )
        
        self.ticket_category = TicketCategory.objects.create(
            event=self.event,
            name='VIP',
            category_type='vip',
            price=100.00,
            initial_tickets=10,
            available_tickets=10
        )
    
    def test_verify_ticket_gate_missing_fields(self):
        """Test endpoint with missing required fields."""
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({'ticket_code': 'TEST'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Missing required fields', data['error'])
    
    def test_verify_ticket_gate_invalid_json(self):
        """Test endpoint with invalid JSON."""
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_verify_ticket_gate_invalid_signature(self):
        """Test endpoint with invalid signature."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='confirmed'
        )
        
        timestamp = timezone.now().isoformat()
        
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({
                'ticket_code': ticket.ticket_code,
                'timestamp': timestamp,
                'signature': '0' * 64
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid signature', data['error'])
    
    def test_verify_ticket_gate_not_found(self):
        """Test endpoint with non-existent ticket."""
        timestamp = timezone.now().isoformat()
        signature = generate_hmac_signature('NONEXISTENT', timestamp)
        
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({
                'ticket_code': 'NONEXISTENT',
                'timestamp': timestamp,
                'signature': signature
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_verify_ticket_gate_already_used(self):
        """Test endpoint with already used ticket."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            total_amount=100.00,
            status='used',
            used_at=timezone.now()
        )
        
        timestamp = timezone.now().isoformat()
        signature = generate_hmac_signature(ticket.ticket_code, timestamp)
        
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({
                'ticket_code': ticket.ticket_code,
                'timestamp': timestamp,
                'signature': signature
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_verify_ticket_gate_success(self):
        """Test successful ticket verification."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test Buyer',
            buyer_email='buyer@test.com',
            quantity=1,
            total_amount=100.00,
            status='confirmed'
        )
        
        timestamp = timezone.now().isoformat()
        signature = generate_hmac_signature(ticket.ticket_code, timestamp)
        
        response = self.client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({
                'ticket_code': ticket.ticket_code,
                'timestamp': timestamp,
                'signature': signature
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('ticket', data)
        self.assertEqual(data['ticket']['status'], 'valid')
        self.assertEqual(data['ticket']['buyer_name'], 'Test Buyer')
        
        # Verify ticket was marked as used
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'used')
    
    def test_validate_gate_signature_valid(self):
        """Test signature validation endpoint with valid signature."""
        timestamp = timezone.now().isoformat()
        ticket_code = 'TEST123'
        signature = generate_hmac_signature(ticket_code, timestamp)
        
        response = self.client.post(
            '/api/v1/gate/validate-signature/',
            data=json.dumps({
                'ticket_code': ticket_code,
                'timestamp': timestamp,
                'signature': signature
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_validate_gate_signature_invalid(self):
        """Test signature validation endpoint with invalid signature."""
        timestamp = timezone.now().isoformat()
        
        response = self.client.post(
            '/api/v1/gate/validate-signature/',
            data=json.dumps({
                'ticket_code': 'TEST123',
                'timestamp': timestamp,
                'signature': '0' * 64
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_endpoint_requires_post(self):
        """Test that endpoint requires POST method."""
        response = self.client.get('/api/v1/gate/verify-ticket/')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


class EdgeCaseTestCase(TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.category = Category.objects.create(
            name='Music',
            slug='music'
        )
        
        self.user = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            is_seller=True
        )
        
        self.event = Event.objects.create(
            organizer=self.user,
            category=self.category,
            title='Test Event',
            slug='test-event',
            date=timezone.now() + timedelta(hours=0.5),
            location='Test Venue'
        )
        
        self.ticket_category = TicketCategory.objects.create(
            event=self.event,
            name='General',
            price=50.00,
            initial_tickets=10,
            available_tickets=10
        )
    
    def test_ticket_code_case_sensitivity(self):
        """Test that ticket codes are case-sensitive."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test',
            buyer_email='test@test.com',
            total_amount=50.00,
            status='confirmed'
        )
        
        # Try to verify with different case
        ticket_data, error_msg = verify_ticket(ticket.ticket_code.lower())
        self.assertEqual(error_msg, "Ticket not found")
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly trimmed in API."""
        ticket = Ticket.objects.create(
            event=self.event,
            ticket_category=self.ticket_category,
            buyer_name='Test',
            buyer_email='test@test.com',
            total_amount=50.00,
            status='confirmed'
        )
        
        timestamp = timezone.now().isoformat()
        signature = generate_hmac_signature(ticket.ticket_code, timestamp)
        
        client = Client()
        response = client.post(
            '/api/v1/gate/verify-ticket/',
            data=json.dumps({
                'ticket_code': f'  {ticket.ticket_code}  ',
                'timestamp': f'  {timestamp}  ',
                'signature': f'  {signature}  '
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
