from django.utils.deprecation import MiddlewareMixin
from .models_analytics import Visitor

class VisitorTrackingMiddleware(MiddlewareMixin):
    """Middleware to track visitor activity"""
    def process_request(self, request):
        # Skip tracking for admin and static/media files
        if request.path.startswith(('/admin/', '/static/', '/media/')):
            return None
            
        # Only track GET requests
        if request.method != 'GET':
            return None
            
        # Ensure session is created/retrieved
        if not hasattr(request, 'session'):
            return None
            
        if not request.session.session_key:
            request.session.save()
            
        # Track the visit
        try:
            Visitor.track_visit(request)
        except Exception as e:
            # Don't break the request if tracking fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error tracking visit: {str(e)}")
            
        return None
