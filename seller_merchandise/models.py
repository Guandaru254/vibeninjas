from django.db import models
from django.conf import settings
from django.utils import timezone

# Import User model to avoid circular import
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    User = None

class SellerMerchandiseCategory(models.Model):
    """Categories for seller merchandise items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Seller Merchandise Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class SellerMerchandise(models.Model):
    """Merchandise items added by sellers for their events"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('sold_out', 'Sold Out'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(SellerMerchandiseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_merchandise')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='seller_merchandise/images/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Seller Merchandise"
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def is_available(self):
        return self.status == 'active' and self.stock_quantity > 0
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('seller_merchandise_detail', kwargs={'pk': self.pk})

class SellerMerchandiseOrder(models.Model):
    """Orders for seller merchandise items"""
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
    ]
    
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_merchandise_orders')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_orders')
    items = models.ManyToManyField(SellerMerchandise, through='SellerOrderItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100, blank=True)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

class SellerOrderItem(models.Model):
    """Individual items within a seller merchandise order"""
    order = models.ForeignKey(SellerMerchandiseOrder, on_delete=models.CASCADE)
    merchandise = models.ForeignKey(SellerMerchandise, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.merchandise.name} - Ksh.{self.price}"
    
    @property
    def total_price(self):
        return self.quantity * self.price
