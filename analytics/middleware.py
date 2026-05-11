from django.utils import timezone
from .models import Visitor
from django.contrib.auth import get_user_model

User = get_user_model()

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Skip tracking for admin, static, and media URLs
        if not any([
            request.path.startswith('/admin/'),
            request.path.startswith('/static/'),
            request.path.startswith('/media/'),
            request.path.startswith('/favicon.ico'),
            '/admin-dashboard/' in request.path  # Skip admin dashboard to avoid tracking admin activity
        ]):
            self.track_visit(request)
            
        response = self.get_response(request)
        return response
    
    def track_visit(self, request):
        """Track the current visit in the database"""
        if not hasattr(request, 'session') or not request.session.session_key:
            return
            
        session_key = request.session.session_key
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        referrer = request.META.get('HTTP_REFERER', '')[:255]
        
        # Only track GET requests
        if request.method != 'GET':
            return
            
        # Get or create visitor record
        user = request.user if request.user.is_authenticated else None
        
        # Create a new visit record for each page view
        Visitor.objects.create(
            session_key=session_key,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            path=request.path,
            visit_type='page_view'
        )
    
    @staticmethod
    def get_client_ip(request):
        """Get the visitor's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
