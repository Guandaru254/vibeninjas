from django.db import models
from django.conf import settings
from events.models import Event, TicketCategory
import uuid


class Transaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('unknown', 'Unknown'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
    )
    transaction_id = models.CharField(max_length=100, unique=True, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    
    # M-Pesa specific fields
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    # merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Event and ticket related fields
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='transactions')
    ticket_category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='transactions')
    buyer_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.buyer_name} - {self.amount} - {self.status}"
# Create your models here.
