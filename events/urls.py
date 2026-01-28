from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_subscription
from django.contrib.auth.decorators import user_passes_test

urlpatterns = [
    path('', views.home, name='home'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    # path('checkout/<int:pk>/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('ticket/<int:ticket_id>/', views.ticket_confirmation, name='ticket_confirmation'),
    
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/buyer/', views.signup_buyer, name='signup_buyer'),
    path('signup/seller/', views.signup_seller, name='signup_seller'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:pk>/', views.edit_event, name='edit_event'),
    path('events/<int:pk>/delete/', views.delete_event, name='delete_event'),

    path('create-payment-intent/<int:pk>/', views.create_payment_intent, name='create_payment_intent'),
    # path('ticket-confirmation/<str:payment_intent>/', views.ticket_confirmation, name='ticket_confirmation'),

    path('subscribe/<str:plan>/', views_subscription.subscribe, name='subscribe'),
    path('subscription/success/', views_subscription.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views_subscription.subscription_cancel, name='subscription_cancel'),
    path('pro-features/', views_subscription.pro_features, name='pro_features'),
    path('subscription/settings/', views_subscription.subscription_settings, name='subscription_settings'),
    
    # Profile Management URLs
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    path('profile/tickets/', views.my_tickets, name='my_tickets'),
    
    # Admin URLs
    path('admin-dashboard/', user_passes_test(lambda u: u.is_staff)(views.admin_dashboard), name='admin_dashboard'),
    
    # M-Pesa Callback URL
    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]
