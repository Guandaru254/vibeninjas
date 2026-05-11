from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Visitor

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'get_username', 'visit_type', 'path_display', 'ip_address', 'browser_display')
    list_filter = ('visit_type', 'timestamp', 'is_mobile', 'is_tablet', 'is_pc', 'is_bot')
    search_fields = ('user__username', 'user__email', 'ip_address', 'path', 'user_agent')
    readonly_fields = ('timestamp', 'session_key', 'user', 'ip_address', 'user_agent', 'referrer', 'path', 'visit_type', 'content_type', 'object_id', 'content_object', 'device_type', 'browser', 'os', 'is_mobile', 'is_tablet', 'is_pc', 'is_bot')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Visit Information', {
            'fields': ('timestamp', 'visit_type', 'path', 'referrer')
        }),
        ('User Information', {
            'fields': ('user', 'session_key', 'ip_address')
        }),
        ('Device Information', {
            'fields': ('user_agent', 'browser', 'os', 'device_type', 'is_mobile', 'is_tablet', 'is_pc', 'is_bot')
        }),
        ('Content Information', {
            'fields': ('content_type', 'object_id', 'content_object'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'Guest'
    get_username.short_description = 'User'
    get_username.admin_order_field = 'user__username'
    
    def path_display(self, obj):
        return obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
    path_display.short_description = 'Path'
    
    def browser_display(self, obj):
        browser = obj.browser or 'Unknown'
        os = f" ({obj.os})" if obj.os else ""
        return f"{browser}{os}"
    browser_display.short_description = 'Browser (OS)'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
