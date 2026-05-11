from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum

User = get_user_model()

class Visitor(models.Model):
    """Model to track website visitors and their activities"""
    VISIT_TYPES = (
        ('page_view', 'Page View'),
        ('event_view', 'Event View'),
        ('ticket_purchase', 'Ticket Purchase'),
        ('signup', 'User Signup'),
    )

    session_key = models.CharField(max_length=40, db_index=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='visits'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    path = models.CharField(max_length=255, db_index=True)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES, default='page_view')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # For tracking specific content (like which event was viewed)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional metadata
    device_type = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    is_mobile = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_key', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['visit_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.visit_type} - {self.path} - {self.timestamp}"
    
    @classmethod
    def track_visit(cls, request, visit_type='page_view', content_object=None, **kwargs):
        """Track a visitor's activity"""
        if not hasattr(request, 'session') or not request.session.session_key:
            return None
            
        # Skip tracking for admin pages and static files
        if request.path.startswith(('/admin/', '/static/', '/media/')):
            return None
            
        user = request.user if request.user.is_authenticated else None
        
        # Get user agent info
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER')
        
        # Get IP address (handling proxy)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create the visit
        visit = cls.objects.create(
            session_key=request.session.session_key,
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            referrer=referrer,
            path=request.path,
            visit_type=visit_type,
            **kwargs
        )
        
        if content_object:
            visit.content_object = content_object
            visit.save()
            
        return visit
    
    @classmethod
    def get_recent_visits(cls, limit=10):
        """Get recent visits with user info if available"""
        return cls.objects.select_related('user').order_by('-timestamp')[:limit]
    
    @classmethod
    def get_visitor_stats(cls, days=30):
        """Get visitor statistics for the last N days"""
        from django.db.models.functions import TruncDate
        from django.utils import timezone
        
        date_from = timezone.now() - timezone.timedelta(days=days)
        
        # Get daily visitor counts
        daily_stats = (
            cls.objects
            .filter(timestamp__gte=date_from)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(visits=Count('id', distinct=True))
            .annotate(users=Count('user', distinct=True))
            .order_by('date')
        )
        
        # Get top pages
        top_pages = (
            cls.objects
            .filter(timestamp__gte=date_from)
            .values('path')
            .annotate(visits=Count('id'))
            .order_by('-visits')[:10]
        )
        
        # Get visit types
        visit_types = (
            cls.objects
            .filter(timestamp__gte=date_from)
            .values('visit_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        return {
            'daily_stats': list(daily_stats),
            'top_pages': list(top_pages),
            'visit_types': list(visit_types),
            'total_visits': sum(day['visits'] for day in daily_stats) if daily_stats else 0,
            'unique_visitors': sum(day['users'] for day in daily_stats) if daily_stats else 0,
        }
