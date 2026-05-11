from django.contrib import admin
from .models_merchandise import Merchandise, MerchandiseCategory, MerchandiseOrder, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('total_price',)
    fields = ('merchandise', 'quantity', 'price', 'total_price')

@admin.register(MerchandiseCategory)
class MerchandiseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'stock_quantity', 'status', 'created_at')
    list_filter = ('status', 'seller_type', 'category', 'created_at')
    search_fields = ('name', 'description', 'seller__username')
    list_editable = ('status', 'stock_quantity', 'price')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'price', 'stock_quantity')
        }),
        ('Seller Information', {
            'fields': ('seller', 'seller_type', 'status')
        }),
        ('Images', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MerchandiseOrder)
class MerchandiseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'status', 'total_amount', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'buyer__username', 'payment_reference')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {
            'fields': ('buyer', 'status', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'merchandise', 'quantity', 'price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'merchandise__name')
    readonly_fields = ('total_price',)
    
    def total_price(self, obj):
        return obj.quantity * obj.price
    total_price.short_description = 'Total Price'
