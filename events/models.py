from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.utils.text import slugify

# Import merchandise models
from .models_merchandise import MerchandiseCategory, Merchandise, MerchandiseOrder, OrderItem

# Conditionally import Cloudinary
if hasattr(settings, 'CLOUDINARY_STORAGE') and settings.CLOUDINARY_STORAGE:
    import cloudinary.models
    ProfilePictureField = cloudinary.models.CloudinaryField('profile_pics', blank=True, null=True)
else:
    ProfilePictureField = models.ImageField(upload_to='profile_pics/', blank=True, null=True)


class User(AbstractUser):
    is_buyer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_pro = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = ProfilePictureField

    business_name = models.CharField(max_length=100, blank=True)
    business_description = models.TextField(blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )

    @property
    def has_active_subscription(self):
        return hasattr(self, 'subscription') and self.subscription.is_active()

    def get_dashboard_url(self):
        if self.is_seller:
            return reverse('dashboard')
        elif self.is_buyer:
            return reverse('home')
        return reverse('home')


class Category(models.Model):
    name = models.CharField(max_length=100, null=False, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Event(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name='events')
    title = models.CharField(max_length=150)
    # Added slug field: unique=True is vital for clean, non-conflicting URLs
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    description = models.TextField()
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=300)
    total_tickets = models.PositiveIntegerField(default=0)
    available_tickets = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # Updated to use slug for professional URLs
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    # Auto-generate slug from title on save
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def tickets_sold(self):
        return sum(
            category.tickets_sold
            for category in self.ticket_categories.all()
        )

    @property
    def is_sold_out(self):
        if not self.ticket_categories.exists():
            return False
        return not self.get_available_categories().exists()

    @property
    def is_past_event(self):
        return self.date < timezone.now()

    @property
    def lowest_ticket_price(self):
        paid_categories = self.ticket_categories.filter(is_free=False).order_by('price')
        category = paid_categories.first()
        return category.price if category else None

    @property
    def highest_ticket_price(self):
        category = self.ticket_categories.order_by('-price').first()
        return category.price if category else None

    @property
    def has_free_tickets(self):
        return self.ticket_categories.filter(is_free=True).exists()

    def get_available_categories(self):
        """Get all available ticket categories — handles null sales windows"""
        from django.db.models import Q
        now = timezone.now()
        return self.ticket_categories.filter(
            available_tickets__gt=0
        ).filter(
            Q(sales_start__isnull=True) | Q(sales_start__lte=now)
        ).filter(
            Q(sales_end__isnull=True) | Q(sales_end__gte=now)
        )

    def get_total_revenue(self):
        return sum(category.get_revenue() for category in self.ticket_categories.all())

class TicketCategory(models.Model):
    CATEGORY_TYPES = [
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('early_bird', 'Early Bird'),
        ('student', 'Student'),
        ('couples', 'Couples Pass'),
        ('group', 'Group / Squad'),
        ('table', 'Table Booking'),
        ('free', 'Free / RSVP'),
        ('press', 'Press / Media'),
        ('backstage', 'Backstage'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='ticket_categories'
    )
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPES,
        default='regular'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    initial_tickets = models.PositiveIntegerField(
        default=0,
        help_text="Initial number of tickets in this category"
    )
    available_tickets = models.PositiveIntegerField(
        default=0,
        help_text="Current number of tickets available"
    )
    description = models.TextField(blank=True)
    max_tickets_per_purchase = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of tickets one person can buy"
    )
    sales_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave blank to start selling immediately"
    )
    sales_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave blank to sell until event date"
    )

    # Bundle / Group fields
    is_bundle = models.BooleanField(
        default=False,
        help_text="Enable for Couple Pass, Squad, Table bookings"
    )
    bundle_size = models.PositiveIntegerField(
        default=1,
        help_text="How many people this ticket admits"
    )
    bundle_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. 'Admits 2', 'Table of 8'"
    )

    # Free / RSVP
    is_free = models.BooleanField(
        default=False,
        help_text="Free / RSVP — no payment required"
    )

    # Display
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first"
    )

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.event.title} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.pk and self.available_tickets:
            self.initial_tickets = self.available_tickets
        if self.price == 0:
            self.is_free = True
        if self.bundle_size > 1:
            self.is_bundle = True
            if not self.bundle_label:
                self.bundle_label = f"Admits {self.bundle_size}"
        super().save(*args, **kwargs)

    @property
    def tickets_sold(self):
        return self.tickets.filter(status='confirmed').aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    def get_sales_percentage(self):
        if not self.initial_tickets:
            return 0
        return min(100, (self.tickets_sold * 100) // self.initial_tickets)

    @property
    def is_available(self):
        now = timezone.now()
        if self.available_tickets <= 0:
            return False
        if self.sales_start and self.sales_start > now:
            return False
        if self.sales_end and self.sales_end < now:
            return False
        return True

    @property
    def effective_price(self):
        if self.is_free:
            return 0
        return self.price

    @property
    def per_person_price(self):
        if self.is_bundle and self.bundle_size > 1 and self.price > 0:
            return round(float(self.price) / self.bundle_size, 2)
        return float(self.price)

    @property
    def total_tickets(self):
        return self.initial_tickets

    def get_revenue(self):
        return sum(ticket.total_amount for ticket in self.tickets.all())


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('used', 'Used'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    ticket_category = models.ForeignKey(
        TicketCategory, on_delete=models.CASCADE,
        null=True, blank=True, related_name='tickets'
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='purchased_tickets', null=True, blank=True
    )
    buyer_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=50, unique=True)
    transaction_code = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    used_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.unit_price and self.ticket_category:
            self.unit_price = self.ticket_category.effective_price
        if self.unit_price is None:
            self.unit_price = 0
        self.total_amount = self.unit_price * self.quantity
        if not self.ticket_code:
            import uuid
            self.ticket_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def mark_as_used(self):
        self.status = 'used'
        self.used_at = timezone.now()
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()


class Subscription(models.Model):
    SUBSCRIPTION_PLANS = [
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('premium', 'Premium'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=100)
    stripe_subscription_id = models.CharField(max_length=100)
    plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_active(self):
        return self.status == 'active' and self.expires_at > timezone.now()

class PromoCode(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (Ksh)'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="The code people type in (e.g. SOUL20)")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount or % value")
    
    # Specifics
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='promo_codes', help_text="Leave blank if valid for ALL events")
    promoter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='promoter_codes', help_text="The DJ or Influencer this code belongs to")
    
    # Constraints
    max_uses = models.PositiveIntegerField(default=0, help_text="0 for unlimited")
    uses_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' Ksh'}"

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def validate(self, event=None):
        """Returns (is_valid, message)"""
        now = timezone.now()
        if not self.is_active:
            return False, "This code is no longer active."
        if self.valid_until and now > self.valid_until:
            return False, "This code has expired."
        if self.max_uses > 0 and self.uses_count >= self.max_uses:
            return False, "This code has reached its usage limit."
        if self.event and event and self.event != event:
            return False, "This code is not valid for this specific event."
        return True, None