from django.contrib import admin
from payments.models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    ordering = ("-timestamp",)
    list_display = ('transaction_id', 'amount', 'event', 'ticket_category', 'buyer_name', 'buyer_email', 'buyer_phone', 'quantity', 'status')
    search_fields = ('phone_number', 'buyer_name', 'buyer_email')
    list_filter = ('status', 'event')

# Register your models here.
