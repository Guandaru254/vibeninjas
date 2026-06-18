from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [

    # M-Pesa STK Push
    path('initiate-mpesa-payment/<slug:slug>/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    
    # M-Pesa Callbacks
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa-callback-test/', views.mpesa_callback_test, name='mpesa_callback_test'),
    
    # Payment Status
    path('check-payment-status/<str:transaction_id>/', views.check_payment_status, name='check_payment_status'),

    # Confirmation
    path('ticket-confirmation/<str:transaction_id>/', views.ticket_confirmation, name='ticket_confirmation'),
    
    # Paystack Integration
    path('initiate-paystack-payment/<slug:slug>/', views.initiate_paystack_payment, name='initiate_paystack_payment'),
    path('paystack-payment-success/<slug:slug>/', views.paystack_payment_success, name='paystack_payment_success'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Legacy Stripe (keep for compatibility)
    path('payment-success/', views.payment_success, name='payment_success'),
]