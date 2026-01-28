
from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('checkout/<int:pk>/', views.checkout, name='checkout'),
    # path('payment-success/', views.payment_success, name='payment_success'),
    
    path('initiate-mpesa-payment/<int:pk>/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check-payment-status/<str:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('ticket-confirmation/<str:transaction_id>/', views.ticket_confirmation, name='ticket_confirmation'),
]