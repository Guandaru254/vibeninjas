from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Event, Ticket, Category, TicketCategory, PromoCode

User = get_user_model()


class TicketCategoryInline(admin.TabularInline):
    model = TicketCategory
    extra = 1
    fields = [
        'name', 'category_type', 'price', 'available_tickets',
        'is_free', 'is_bundle', 'bundle_size',
        'sales_start', 'sales_end', 'display_order'
    ]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'date', 'lowest_ticket_price', 'tickets_sold', 'is_active']
    list_filter = ['is_active', 'date', 'created_at']
    search_fields = ['title', 'description', 'location']
    list_editable = ['is_active']
    inlines = [TicketCategoryInline]

    def lowest_ticket_price(self, obj):
        return f"Ksh {obj.lowest_ticket_price}" if obj.lowest_ticket_price else "Free / No price"
    lowest_ticket_price.short_description = "Starting Price"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_code', 'buyer_name', 'event',
        'ticket_category', 'quantity', 'total_amount', 'status', 'purchased_at'
    ]
    list_filter = ['status', 'purchased_at', 'event']
    search_fields = ['buyer_name', 'buyer_email', 'ticket_code']
    readonly_fields = ['ticket_code', 'purchased_at', 'unit_price', 'total_amount']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'event', 'category_type', 'price',
        'available_tickets', 'is_free', 'is_bundle', 'bundle_size', 'sales_status'
    ]
    list_filter = ['category_type', 'is_free', 'is_bundle', 'event']
    search_fields = ['name', 'event__title']
    readonly_fields = ['sales_status', 'tickets_sold']

    def sales_status(self, obj):
        if obj.available_tickets <= 0:
            return "Sold Out"
        now = timezone.now()
        if obj.sales_start and obj.sales_start > now:
            return f"Starts {obj.sales_start.strftime('%b %d')}"
        if obj.sales_end and obj.sales_end < now:
            return "Ended"
        return "Available"
    sales_status.short_description = "Status"


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_seller', 'is_buyer')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_seller', 'is_buyer')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


try:
    admin.site.register(User, CustomUserAdmin)
except admin.sites.AlreadyRegistered:
    admin.site.unregister(User)
    admin.site.register(User, CustomUserAdmin)
except Exception as e:
    print(f"Error registering User model: {e}")


class GroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

from .admin_merchandise import *

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'event', 'uses_count', 'is_active')
    list_filter = ('discount_type', 'is_active', 'event')
    search_fields = ('code',)
    readonly_fields = ('uses_count',) # Don't let people manually edit the count easily