from django.urls import path
from . import views, views_subscription
from django.contrib.auth.decorators import user_passes_test, login_required
from seller_merchandise import views as seller_merchandise_views

urlpatterns = [
    # ─── MAIN EVENT FLOW ──────────────────────────────────────────────────────
    path('', views.home, name='home'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('checkout/<int:pk>/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('ticket/<int:ticket_id>/', views.ticket_confirmation, name='ticket_confirmation'),
    
    # ─── ACCOUNTS & DASHBOARD ─────────────────────────────────────────────────
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/buyer/', views.signup_buyer, name='signup_buyer'),
    path('signup/seller/', views.signup_seller, name='signup_seller'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ─── EVENT MANAGEMENT ─────────────────────────────────────────────────────
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:pk>/', views.edit_event, name='edit_event'),
    path('events/<int:pk>/delete/', views.delete_event, name='delete_event'),
    
    # ─── SUBSCRIPTIONS ────────────────────────────────────────────────────────
    path('subscribe/<str:plan>/', views_subscription.subscribe, name='subscribe'),
    path('subscription/success/', views_subscription.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views_subscription.subscription_cancel, name='subscription_cancel'),
    path('pro-features/', views_subscription.pro_features, name='pro_features'),
    path('subscription/settings/', views_subscription.subscription_settings, name='subscription_settings'),
    
    # ─── PROFILE & USER DATA ──────────────────────────────────────────────────
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    path('profile/tickets/', views.my_tickets, name='my_tickets'),
    
    # ─── SELLER MERCHANDISE ───────────────────────────────────────────────────
    path('seller/dashboard/', login_required(seller_merchandise_views.seller_merchandise_dashboard), name='seller_dashboard'),
    path('merchandise/add/', login_required(seller_merchandise_views.SellerMerchandiseCreateView.as_view()), name='merchandise_add'),
    path('merchandise/orders/', login_required(seller_merchandise_views.seller_merchandise_order_list), name='merchandise_order_list'),
    path('merchandise/orders/<int:pk>/', login_required(seller_merchandise_views.seller_merchandise_order_detail), name='merchandise_order_detail'),
    path('seller/merchandise/list/', login_required(seller_merchandise_views.SellerMerchandiseListView.as_view()), name='seller_merchandise_list'),
    path('seller/merchandise/<int:pk>/edit/', login_required(seller_merchandise_views.SellerMerchandiseUpdateView.as_view()), name='seller_merchandise_edit'),
    path('seller/merchandise/<int:pk>/delete/', login_required(seller_merchandise_views.SellerMerchandiseDeleteView.as_view()), name='seller_merchandise_delete'),
    
    # ─── PUBLIC SHOP ──────────────────────────────────────────────────────────
    path('shop/', seller_merchandise_views.PublicMerchandiseListView.as_view(), name='public_merchandise_list'),
    path('shop/<int:pk>/', seller_merchandise_views.PublicMerchandiseDetailView.as_view(), name='public_merchandise_detail'),
    path('my-merchandise-orders/', views.buyer_merchandise_order_list, name='buyer_merchandise_order_list'),
    
    # ─── UTILS & API ──────────────────────────────────────────────────────────
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('admin-dashboard/', user_passes_test(lambda u: u.is_staff)(views.admin_dashboard), name='admin_dashboard'),
    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('create-payment-intent/<int:pk>/', views.create_payment_intent, name='create_payment_intent'),
]