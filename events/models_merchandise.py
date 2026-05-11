from django.db import models
from django.conf import settings
from django.utils import timezone

class MerchandiseCategory(models.Model):
    """Categories for merchandise items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Merchandise Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Merchandise(models.Model):
    """Merchandise items that can be sold on the platform"""
    SELLER_TYPES = [
        ('admin', 'Admin'),
        ('seller', 'Event Seller'),
    ]
    
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
    category = models.ForeignKey(MerchandiseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey('events.User', on_delete=models.CASCADE, related_name='merchandise')
    seller_type = models.CharField(max_length=10, choices=SELLER_TYPES, default='seller')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='merchandise/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Merchandise"
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def is_available(self):
        return self.status == 'active' and self.stock_quantity > 0
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('merchandise_detail', kwargs={'pk': self.pk})

class MerchandiseOrder(models.Model):
    """Orders for merchandise items"""
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
    
    buyer = models.ForeignKey('events.User', on_delete=models.CASCADE, related_name='merchandise_orders')
    items = models.ManyToManyField(Merchandise, through='OrderItem')
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

class OrderItem(models.Model):
    """Individual items within an order"""
    order = models.ForeignKey(MerchandiseOrder, on_delete=models.CASCADE)
    merchandise = models.ForeignKey(Merchandise, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.merchandise.name} - Ksh.{self.price}"
    
    @property
    def total_price(self):
        return self.quantity * self.price
