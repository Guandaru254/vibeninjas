from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from django.core.serializers.json import DjangoJSONEncoder
from .forms import BuyerSignUpForm, SellerSignUpForm, BuyerProfileForm, SellerProfileForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Category, Event, Ticket, TicketCategory, PromoCode
from .forms import EventForm, TicketCategoryFormSet, TicketPurchaseForm
from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal
import io
import os
import json
import base64
import requests
import logging
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.views.decorators.vary import vary_on_cookie


User = get_user_model()

logger = logging.getLogger(__name__)

# ============================================================================
# STATIC PAGES
# ============================================================================

def privacy_policy(request):
    """Privacy Policy page view"""
    return render(request, 'privacy_policy.html')

"""
AUTHENTICATION VIEWS ONLY - Replace in your views.py
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .forms import BuyerSignUpForm, SellerSignUpForm

User = get_user_model()


# ════════════════════════════════════════════════════════════════════
# FIXED AUTHENTICATION VIEWS
# ════════════════════════════════════════════════════════════════════

class CustomLoginView(LoginView):
    """
    FIXED Login View with correct role-based redirects
    """
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        """
        Redirect based on role - CORRECTED PRIORITY
        """
        user = self.request.user
        
        # Safe attribute checking
        is_seller = getattr(user, 'is_seller', False)
        is_buyer = getattr(user, 'is_buyer', False)
        is_staff = getattr(user, 'is_staff', False)
        
        # Priority 1: Admin (staff with no seller/buyer role)
        if is_staff and not is_seller and not is_buyer:
            return '/admin-dashboard/'
        
        # Priority 2: Sellers
        if is_seller:
            return '/dashboard/'
        
        # Priority 3: Buyers
        if is_buyer:
            return '/'
        
        # Default
        return '/'


@require_POST  # CRITICAL: Only POST allowed
def custom_logout(request):
    """
    FIXED Logout - POST only for security
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


def signup_buyer(request):
    """Buyer signup"""
    if request.method == 'POST':
        form = BuyerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BuyerSignUpForm()
    
    return render(request, 'registration/buyer-signup.html', {'form': form})


def signup_seller(request):
    """Seller signup"""
    if request.method == 'POST':
        form = SellerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SellerSignUpForm()
    
    return render(request, 'registration/seller-signup.html', {'form': form})

# ============================================================================
# PUBLIC EVENT VIEWS
# ============================================================================
@vary_on_cookie
def home(request):
    """Home page with upcoming events"""
    events = Event.objects.filter(
        is_active=True, 
        date__gte=timezone.now()
    ).prefetch_related('ticket_categories').order_by('date')[:6]
    
    return render(request, 'events/home.html', {
        'events': events
    })

@vary_on_cookie
def event_list(request):
    """List all events with separate upcoming and past sections"""
    now = timezone.now()
    
    # Base queryset for active events
    base_events = Event.objects.filter(is_active=True)
    categories = Category.objects.all()

    search_query = request.GET.get('search', '')
    category_slug = request.GET.get('category', '')

    # Apply Search & Category filters to the base
    if search_query:
        base_events = base_events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if category_slug:
        base_events = base_events.filter(category__slug=category_slug)

    # ══════════════════════════════════════════════════════════
    # SPLIT LOGIC: Upcoming vs Past
    # ══════════════════════════════════════════════════════════
    upcoming_events = base_events.filter(date__gte=now).prefetch_related('ticket_categories').order_by('date')
    past_events = base_events.filter(date__lt=now).prefetch_related('ticket_categories').order_by('-date')[:6] # Limit past to last 6

    return render(request, 'events/event_list.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_slug
    })

@login_required
def category_events(request, slug):
    """Events filtered by category"""
    category = get_object_or_404(Category, slug=slug)
    events = Event.objects.filter(category=category)
    return render(request, 'events/category_events.html', {'category': category, 'events': events})

def event_detail(request, slug):
    """Event detail page with Promo Link Catcher"""
    event = get_object_or_404(Event, slug=slug)
    
    # ══════════════════════════════════════════════════════════
    # THE PROMO LINK CATCHER
    # Captures ?promo=MAGIK from URL and stores it in session
    # ══════════════════════════════════════════════════════════
    promo_from_url = request.GET.get('promo')
    if promo_from_url:
        # We strip and uppercase to keep data clean
        request.session['promo_code'] = promo_from_url.upper().strip()

    # Your existing logic for the first available ticket
    selected_category = event.ticket_categories.filter(
        available_tickets__gt=0
    ).first()

    context = {
        'event': event,
        'now': timezone.now(),
        'selected_category': selected_category,
        # Pass the stored promo to the template so we can show "Promo Applied" UI
        'active_promo': request.session.get('promo_code'),
    }
    return render(request, 'events/event_detail.html', context)

@require_POST
def validate_promo_code(request):
    # 1. Get data from the POST request
    code = request.POST.get('code', '').strip().upper()
    event_id = request.POST.get('event_id') # This is now the slug string
    current_total = Decimal(request.POST.get('total', '0'))

    try:
        # 2. Fetch the active promo code
        promo = PromoCode.objects.get(code=code, is_active=True)
        
        # 3. FIX: Fetch event by SLUG since the frontend is sending the slug
        event = Event.objects.filter(slug=event_id).first()
        
        if not event:
            return JsonResponse({
                'valid': False, 
                'message': 'Event validation failed. Please refresh the page.'
            })
        
        # 4. Use the Model's validation method (checks expiry, usage, and event match)
        is_valid, message = promo.validate(event=event)
        
        if not is_valid:
            return JsonResponse({'valid': False, 'message': message})

        # 5. Calculate the discount
        if promo.discount_type == 'percentage':
            discount_amount = (promo.discount_value / Decimal('100')) * current_total
        else:
            discount_amount = promo.discount_value

        # 6. Calculate the final price (ensure it doesn't go below 0)
        new_total = max(current_total - discount_amount, Decimal('0'))

        return JsonResponse({
            'valid': True,
            'message': f'Promo applied! You save Ksh {discount_amount:.0f}',
            'discount_amount': float(discount_amount),
            'new_total': float(new_total)
        })

    except PromoCode.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid promo code.'})
    except Exception as e:
        # Catch-all for any unexpected math or decimal errors
        return JsonResponse({'valid': False, 'message': 'An error occurred during validation.'})





# ============================================================================
# SELLER DASHBOARD & EVENT MANAGEMENT - NEW IMPROVED VERSION
# ============================================================================

@login_required
def dashboard(request):
    """
    Enhanced Seller Dashboard - "My Shop" 
    NEW: Time period filters, charts, full event list with delete
    """
    # Block buyers from accessing seller dashboard
    if not request.user.is_seller:
        messages.info(request, 'The dashboard is for event organizers and sellers.')
        return redirect('home')
    
    # Get time period from URL param (default: 30 days)
    period = request.GET.get('period', '30d')
    now = timezone.now()
    
    # Calculate date ranges based on selected period
    if period == '7d':
        start_date = now - timedelta(days=7)
        prev_start = start_date - timedelta(days=7)
    elif period == '90d':
        start_date = now - timedelta(days=90)
        prev_start = start_date - timedelta(days=90)
    elif period == 'all':
        start_date = None
        prev_start = None
    else:  # Default: 30d
        period = '30d'
        start_date = now - timedelta(days=30)
        prev_start = start_date - timedelta(days=30)
    
    # Get all events for this seller
    events = Event.objects.filter(organizer=request.user).prefetch_related('ticket_categories')
    total_events = events.count()
    
    # ═══════════════════════════════════════════════════════════════
    # REVENUE & SALES METRICS
    # ═══════════════════════════════════════════════════════════════
    
    all_tickets = Ticket.objects.filter(event__organizer=request.user)
    
    # Total Revenue (all time)
    total_revenue = all_tickets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Revenue this month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_this_month = all_tickets.filter(
        purchased_at__gte=month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Tickets sold (period-based)
    if start_date:
        period_tickets = all_tickets.filter(purchased_at__gte=start_date)
    else:
        period_tickets = all_tickets
    
    total_tickets_sold = period_tickets.count()
    
    # Tickets sold today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tickets_sold_today = all_tickets.filter(purchased_at__gte=today_start).count()
    
    # Average ticket price
    avg_ticket_price = period_tickets.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    
    # ═══════════════════════════════════════════════════════════════
    # CONVERSION & ENGAGEMENT METRICS
    # ═══════════════════════════════════════════════════════════════
    
    # Total capacity across all events
    total_capacity = 0
    for event in events:
        if hasattr(event, 'ticket_categories'):
            cap = event.ticket_categories.aggregate(total=Sum('initial_tickets'))['total']
            if cap:
                total_capacity += cap
        elif hasattr(event, 'total_tickets') and event.total_tickets:
            total_capacity += event.total_tickets
    
    # Occupancy rate (tickets sold / total capacity)
    all_tickets_count = all_tickets.count()
    occupancy_rate = (all_tickets_count / total_capacity * 100) if total_capacity > 0 else 0
    
    # Active events (future events with tickets available)
    active_events_count = events.filter(
        date__gte=now,
        is_active=True,
        available_tickets__gt=0
    ).count()
    
    # Sold out events
    sold_out_events = events.filter(available_tickets=0).count()
    
    # Conversion rate (same as occupancy rate in this context)
    conversion_rate = occupancy_rate
    
    # ═══════════════════════════════════════════════════════════════
    # REVENUE CHART DATA (Time-based)
    # ═══════════════════════════════════════════════════════════════
    
    revenue_labels = []
    revenue_data = []
    
    if period == '7d':
        # Daily for last 7 days
        for i in range(7):
            date = now - timedelta(days=6-i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_revenue = Ticket.objects.filter(
                event__organizer=request.user,
                purchased_at__gte=day_start,
                purchased_at__lte=day_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_labels.append(date.strftime('%a'))
            revenue_data.append(float(day_revenue))
    
    elif period == '30d':
        # Daily for last 30 days
        for i in range(30):
            date = now - timedelta(days=29-i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_revenue = Ticket.objects.filter(
                event__organizer=request.user,
                purchased_at__gte=day_start,
                purchased_at__lte=day_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_labels.append(date.strftime('%d'))
            revenue_data.append(float(day_revenue))
    
    elif period == '90d':
        # Weekly for last 90 days
        for i in range(13):
            week_start = now - timedelta(days=90 - (i*7))
            week_end = week_start + timedelta(days=6)
            
            week_revenue = Ticket.objects.filter(
                event__organizer=request.user,
                purchased_at__gte=week_start,
                purchased_at__lte=week_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_labels.append(week_start.strftime('%b %d'))
            revenue_data.append(float(week_revenue))
    
    else:  # all time
        # Monthly for last 6 months
        for i in range(6):
            month_date = now - timedelta(days=30*i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if i == 0:
                month_end = now
            else:
                next_month = month_start + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(seconds=1)
            
            month_revenue = Ticket.objects.filter(
                event__organizer=request.user,
                purchased_at__gte=month_start,
                purchased_at__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_labels.insert(0, month_start.strftime('%b'))
            revenue_data.insert(0, float(month_revenue))
    
    # ═══════════════════════════════════════════════════════════════
    # SALES BY CATEGORY CHART DATA
    # ═══════════════════════════════════════════════════════════════
    
    category_labels = []
    category_data = []
    
    # Get top 5 ticket categories by sales
    category_stats = TicketCategory.objects.filter(
        event__organizer=request.user
    ).annotate(
        sold=Count('tickets')
    ).order_by('-sold')[:5]
    
    for cat in category_stats:
        if cat.sold > 0:
            category_labels.append(cat.name)
            category_data.append(cat.sold)
    
    # If no categories, add default
    if not category_labels:
        category_labels = ['No Sales Yet']
        category_data = [0]
    
    # ═══════════════════════════════════════════════════════════════
    # EVENTS LIST WITH METRICS (for event cards)
    # ═══════════════════════════════════════════════════════════════
    
    events_list = []
    for event in events.select_related().prefetch_related('ticket_categories'):
        # Calculate event-specific metrics
        event_tickets = Ticket.objects.filter(event=event)
        tickets_count = event_tickets.count()
        
        event_revenue = event_tickets.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Calculate capacity
        if hasattr(event, 'ticket_categories'):
            capacity = event.ticket_categories.aggregate(
                total=Sum('initial_tickets')
            )['total'] or 0
        elif hasattr(event, 'total_tickets'):
            capacity = event.total_tickets or 0
        else:
            capacity = 0
        
        events_list.append({
            'slug': event.slug,
            'title': event.title,
            'image': event.image if hasattr(event, 'image') else None,
            'date': event.date,
            'tickets_count': tickets_count,
            'capacity': capacity,
            'revenue': event_revenue,
        })
    
    # ═══════════════════════════════════════════════════════════════
    # TOP PERFORMING EVENTS (for old dashboard compatibility)
    # ═══════════════════════════════════════════════════════════════
    
    top_events = events.annotate(
        revenue=Sum('tickets__total_amount'),
        tickets_count=Count('tickets')
    ).order_by('-revenue')[:5]
    
    # ═══════════════════════════════════════════════════════════════
    # RECENT SALES (Last 10 tickets)
    # ═══════════════════════════════════════════════════════════════
    
    recent_sales = all_tickets.select_related(
        'event', 'ticket_category'
    ).order_by('-purchased_at')[:10]
    
    # ═══════════════════════════════════════════════════════════════
    # MERCHANDISE STATS
    # ═══════════════════════════════════════════════════════════════
    
    try:
        from seller_merchandise.models import SellerMerchandise
        total_products = SellerMerchandise.objects.filter(seller=request.user).count()
    except Exception:
        total_products = 0
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXT DATA
    # ═══════════════════════════════════════════════════════════════
    
    context = {
        # Period
        'period': period,
        
        # Events
        'events': events_list,  # NEW: Full list for cards
        'total_events': total_events,
        'active_events_count': active_events_count,
        'sold_out_events': sold_out_events,
        
        # Revenue
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'avg_ticket_price': avg_ticket_price,
        
        # Tickets
        'total_tickets_sold': total_tickets_sold,
        'tickets_sold_today': tickets_sold_today,
        'total_capacity': total_capacity,
        'occupancy_rate': round(occupancy_rate, 1),
        'conversion_rate': round(conversion_rate, 1),
        
        # Performance (for old template compatibility)
        'top_events': top_events,
        'recent_sales': recent_sales,
        
        # Charts (NEW: JSON for Chart.js)
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_data': json.dumps(revenue_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        
        # Merchandise
        'total_products': total_products,
    }
    
    return render(request, 'events/dashboard.html', context)





@login_required
def delete_event(request, slug):
    """
    Delete an event - AJAX-friendly version using SLUG
    """
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    
    if request.method == 'DELETE':
        tickets_sold = Ticket.objects.filter(event=event).count()
        
        if tickets_sold > 0:
            return JsonResponse({
                'error': f'Cannot delete event with {tickets_sold} sold tickets. Contact support.'
            }, status=400)
        
        event_title = event.title
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Event "{event_title}" deleted successfully'
        })
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('dashboard')
    
    return render(request, 'events/delete.html', {'event': event})


@login_required
def create_event(request):
    """Create a new event with ticket categories - Slug-ready"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        ticket_formset = TicketCategoryFormSet(request.POST)

        if form.is_valid() and ticket_formset.is_valid():
            event = None # Initialize for the except block
            try:
                event = form.save(commit=False)
                event.organizer = request.user
                event.available_tickets = 0
                # slug is auto-generated in model save()
                event.save()

                ticket_formset.instance = event
                categories = ticket_formset.save(commit=False)

                if not categories:
                    messages.error(request, 'Please add at least one ticket category.')
                    event.delete()
                    return render(request, 'events/create_event.html', {
                        'form': form,
                        'ticket_formset': ticket_formset
                    })

                for category in categories:
                    if category.is_free:
                        category.price = Decimal('0.00')
                    if not category.is_bundle:
                        category.bundle_size = 1
                        category.bundle_label = ''
                    if not category.max_tickets_per_purchase:
                        category.max_tickets_per_purchase = 10
                    category.save()

                for obj in ticket_formset.deleted_objects:
                    obj.delete()

                total_available = sum(tc.available_tickets for tc in categories)
                event.available_tickets = total_available
                event.total_tickets = total_available
                event.save()

                messages.success(request, 'Event created successfully!')
                return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'Error creating event: {str(e)}')
                if event and event.id:
                    event.delete()
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()
        ticket_formset = TicketCategoryFormSet()

    return render(request, 'events/create_event.html', {
        'form': form,
        'ticket_formset': ticket_formset
    })


@login_required
def edit_event(request, slug):
    """Edit an existing event using SLUG"""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        ticket_formset = TicketCategoryFormSet(request.POST, instance=event)

        if form.is_valid() and ticket_formset.is_valid():
            try:
                # This will update the slug if the title changed
                event = form.save(commit=False)
                
                categories = ticket_formset.save(commit=False)
                for category in categories:
                    if category.is_free:
                        category.price = Decimal('0.00')
                    if not category.is_bundle:
                        category.bundle_size = 1
                    category.save()

                for obj in ticket_formset.deleted_objects:
                    obj.delete()

                event.available_tickets = sum(
                    tc.available_tickets for tc in event.ticket_categories.all()
                )
                event.save()

                messages.success(request, 'Event updated successfully!')
                return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'Error saving event: {str(e)}')
    else:
        form = EventForm(instance=event)
        ticket_formset = TicketCategoryFormSet(instance=event)

    return render(request, 'events/edit_event.html', {
        'form': form,
        'ticket_formset': ticket_formset,
        'event': event
    })

# ============================================================================
# CHECKOUT & PAYMENT PROCESSING (M-PESA ONLY)
# ============================================================================

def checkout(request, slug):
    """
    Checkout page.
    - Uses 'slug' instead of 'pk' for cleaner, SEO-friendly URLs.
    - Free/RSVP tickets: bypass M-Pesa entirely.
    - Bundle tickets: use effective_price, show people count.
    - Paid tickets: handles promo code re-verification on POST for security.
    """
    # 1. Fetch event by slug instead of ID
    event = get_object_or_404(Event, slug=slug)
    tickets_param = request.GET.get('tickets', '')

    if not tickets_param:
        messages.error(request, 'Please select at least one ticket.')
        return redirect('event_detail', slug=event.slug)

    try:
        ticket_selections = []
        total_amount = Decimal('0')

        for ticket_str in tickets_param.split(','):
            parts = ticket_str.split(':')
            if len(parts) != 2:
                raise ValueError("Malformed ticket parameter")

            category_id = int(parts[0])
            quantity = int(parts[1])

            if quantity < 1:
                raise ValueError("Quantity must be at least 1")

            category = TicketCategory.objects.get(
                id=category_id,
                event=event,
                available_tickets__gte=quantity
            )

            # Always use effective_price (respects is_free flag)
            unit_price = category.effective_price
            subtotal = unit_price * quantity
            total_amount += subtotal

            ticket_selections.append({
                'category': category,
                'quantity': quantity,
                'subtotal': subtotal,
                'unit_price': unit_price,
                'total_people': quantity * category.bundle_size,
                'is_free': category.is_free,
                'is_bundle': category.is_bundle,
                'bundle_label': category.bundle_label,
                'bundle_size': category.bundle_size,
            })

        if not ticket_selections:
            raise ValueError("No valid tickets selected")

    except (ValueError, TicketCategory.DoesNotExist):
        messages.error(request, 'Invalid ticket selection. Please try again.')
        return redirect('event_detail', slug=event.slug)

    # Determine if ALL selected tickets are free
    all_free = all(s['is_free'] for s in ticket_selections)

    # Free RSVP: handle POST directly here
    if all_free and request.method == 'POST':
        return handle_free_rsvp(request, event, ticket_selections)

    initial_data = {}
    if request.user.is_authenticated:
        initial_data.update({
            'buyer_name': request.user.get_full_name() or '',
            'buyer_email': request.user.email or ''
        })

    from .forms import TicketPurchaseForm # Ensure local import if needed
    form = TicketPurchaseForm(event, initial=initial_data)
    
    # Grab the promo from the session (where the Link Catcher put it)
    active_promo = request.session.get('promo_code', '')

    # ══════════════════════════════════════════════════════════
    # SERVER-SIDE PROMO RE-VALIDATION (The Security Bridge)
    # ══════════════════════════════════════════════════════════
    final_amount = total_amount # Default to full price

    if request.method == 'POST' and not all_free:
        # Check hidden input from JS or the session catcher
        code = request.POST.get('promo_code_used') or request.session.get('promo_code')
        
        if code:
            try:
                # Strip spaces and uppercase to match DB
                promo = PromoCode.objects.get(code=code.strip().upper(), is_active=True, event=event)
                is_valid, _ = promo.validate(event=event)
                
                if is_valid:
                    if promo.discount_type == 'percentage':
                        discount = (promo.discount_value / Decimal('100')) * total_amount
                    else:
                        discount = promo.discount_value
                    final_amount = total_amount - discount
            except PromoCode.DoesNotExist:
                pass 
        
        # NOTE: When you trigger M-Pesa STK Push from the frontend AJAX, 
        # that logic is usually in your 'initiate_mpesa_payment' view.
        # This block is here for standard form submissions.

    context = {
        'event': event,
        'ticket_selections': ticket_selections,
        'total_amount': total_amount,
        'final_amount': final_amount, # Pass the discounted amount to context
        'tickets_param': tickets_param,
        'form': form,
        'all_free': all_free,
        'active_promo': active_promo,
    }

    return render(request, 'events/checkout.html', context)




# ============================================================================
# TICKET MANAGEMENT & DELIVERY
# ============================================================================

def ticket_confirmation(request, ticket_id):
    """Display ticket confirmation by ticket ID"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'events/ticket_confirmation.html', {'ticket': ticket})


@login_required
def generate_ticket_image(ticket):
    """Generate a ticket image with event and buyer details"""
    width = 1000
    height = 500
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 25)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((50, 50), ticket.event.title, fill='black', font=font_large)
    draw.text((50, 100), f"Category: {ticket.ticket_category.name}", fill='black', font=font_medium)
    draw.text((50, 150), f"Date: {ticket.event.date.strftime('%B %d, %Y at %I:%M %p')}", fill='black', font=font_medium)
    draw.text((50, 200), f"Location: {ticket.event.location}", fill='black', font=font_medium)
    draw.text((50, 250), f"Attendee: {ticket.buyer_name}", fill='black', font=font_medium)
    draw.text((50, 300), f"Quantity: {ticket.quantity}", fill='black', font=font_medium)
    draw.text((50, 350), f"Price per ticket: Ksh {ticket.unit_price}", fill='black', font=font_medium)
    draw.text((50, 400), f"Ticket Code: {ticket.ticket_code}", fill='black', font=font_large)
    
    image_buffer = io.BytesIO()
    image.save(image_buffer, format='JPEG', quality=90)
    image_buffer.seek(0)
    
    return image_buffer


def send_ticket_email(ticket):
    """Send email with ticket details and attached ticket image"""
    subject = f'Your Ticket for {ticket.event.title}'
    message = f"""
    Dear {ticket.buyer_name},
    
    Thank you for purchasing tickets for {ticket.event.title}!
    
    Event Details:
    - Event: {ticket.event.title}
    - Category: {ticket.ticket_category.name}
    - Date: {ticket.event.date.strftime('%B %d, %Y at %I:%M %p')}
    - Location: {ticket.event.location}
    - Quantity: {ticket.quantity}
    - Price per ticket: Ksh {ticket.unit_price}
    - Total Paid: Ksh {ticket.total_amount}
    - Ticket Code: {ticket.ticket_code}
    
    Please find your ticket attached to this email.
    Present this ticket (either digital or printed) at the event entrance.
    
    Best regards,
    ZOZAPRIME Team
    """
    
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [ticket.buyer_email]
    )
    
    ticket_image = generate_ticket_image(ticket)
    email.attach(
        f'ticket_{ticket.ticket_code}.jpg',
        ticket_image.getvalue(),
        'image/jpeg'
    )
    
    email.send(fail_silently=False)






# ============================================================================
# RSVP & FREE EVENTS
# ============================================================================

def handle_free_rsvp(request, event, ticket_selections):
    """
    Handles RSVP / free ticket confirmation.
    Creates confirmed Ticket records immediately — no payment needed.
    """
    buyer_name = request.POST.get('buyer_name', '').strip()
    buyer_email = request.POST.get('buyer_email', '').strip()

    if not buyer_name or not buyer_email:
        messages.error(request, 'Please provide your name and email for the RSVP.')
        return redirect('event_detail', slug=event.slug)

    created_tickets = []

    try:
        for selection in ticket_selections:
            category = selection['category']
            quantity = selection['quantity']

            # Re-check availability (race condition safety)
            category.refresh_from_db()
            if category.available_tickets < quantity:
                messages.error(
                    request,
                    f'Sorry — only {category.available_tickets} spot(s) left for {category.name}.'
                )
                return redirect('event_detail', slug=event.slug)

            ticket = Ticket.objects.create(
                event=event,
                ticket_category=category,
                buyer_name=buyer_name,
                buyer_email=buyer_email,
                quantity=quantity,
                unit_price=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                status='confirmed',
            )

            # Decrement availability
            category.available_tickets -= quantity
            category.save(update_fields=['available_tickets'])
            created_tickets.append(ticket)

        # TODO: send_ticket_email(created_tickets[0]) — once Zoho/Resend is live

        messages.success(request, "You're in! Check your email for your RSVP confirmation.")
        return redirect('ticket_confirmation', ticket_id=created_tickets[0].id)

    except Exception as e:
        logger.error(f"[FREE_RSVP] Error: {str(e)}", exc_info=True)
        messages.error(request, 'Something went wrong with your RSVP. Please try again.')
        return redirect('event_detail', slug=event.slug)






# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

SUBSCRIPTION_PLANS = {
    'daily': {
        'name': 'Daily Plan',
        'price_id': 'price_XXXXX', 
        'amount': 500,
    },
    'monthly': {
        'name': 'Monthly Plan',
        'price_id': 'price_XXXXX',  
        'amount': 4900,
    },
    'yearly': {
        'name': 'Yearly Plan',
        'price_id': 'price_XXXXX',  
        'amount': 39900,
    }
}


@login_required
def subscription(request, plan):
    """Handle subscription checkout"""
    if plan not in SUBSCRIPTION_PLANS:
        messages.error(request, 'Invalid subscription plan')
        return redirect('dashboard')
    
    plan_data = SUBSCRIPTION_PLANS[plan]
    messages.info(request, 'Subscription feature coming soon!')
    return redirect('dashboard')


@login_required
def subscription_success(request):
    """Subscription success page"""
    messages.success(request, 'Successfully subscribed to ZOZAPRIME Pro!')
    return redirect('dashboard')


@login_required
def subscription_cancel(request):
    """Subscription cancellation page"""
    messages.info(request, 'Subscription cancelled')
    return redirect('dashboard')


@login_required
def pro_features(request):
    """Display pro features page"""
    return render(request, 'subscription/pro_features.html')


@login_required
def subscription_settings(request):
    """Display subscription settings"""
    return render(request, 'subscription/settings.html')





# ============================================================================
# ADMIN DASHBOARD - UPDATED WITH 5 NEW METRICS
# ============================================================================

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive analytics - WITH 5 NEW METRICS"""
    if not request.user.is_staff:
        return redirect('home')
    
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # ═══════════════════════════════════════════════════════════════
    # EXISTING METRICS
    # ═══════════════════════════════════════════════════════════════
    
    # User statistics
    total_users = User.objects.count()
    new_users_week = User.objects.filter(
        date_joined__gte=now - timedelta(days=7)
    ).count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Ticket statistics
    total_tickets = Ticket.objects.count()
    tickets_today = Ticket.objects.filter(
        purchased_at__date=now.date()
    ).count()
    total_revenue = Ticket.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Average ticket price
    avg_ticket_price = Ticket.objects.aggregate(
        avg=Avg('total_amount')
    )['avg'] or Decimal('0.00')
    
    # Tickets this week
    tickets_this_week = Ticket.objects.filter(
        purchased_at__gte=now - timedelta(days=7)
    ).count()
    
    # Event statistics
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(date__gte=now).count()
    
    # M-Pesa stats
    mpesa_success_rate = 0
    mpesa_total_attempts = 0
    try:
        from payments.models import Transaction
        mpesa_total_attempts = Transaction.objects.count()
        mpesa_successful = Transaction.objects.filter(status='success').count()
        if mpesa_total_attempts > 0:
            mpesa_success_rate = round((mpesa_successful / mpesa_total_attempts) * 100)
    except Exception:
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # NEW METRIC 1: ACTIVE SELLERS
    # ═══════════════════════════════════════════════════════════════
    active_sellers = User.objects.filter(
        is_seller=True,
        events__isnull=False
    ).distinct().count()
    
    # ═══════════════════════════════════════════════════════════════
    # NEW METRIC 2: CONVERSION RATE (Visitors to Buyers)
    # ═══════════════════════════════════════════════════════════════
    try:
        from analytics.models import Visit
        total_visits = Visit.objects.filter(
            timestamp__gte=thirty_days_ago
        ).count()
        unique_visitors = Visit.objects.filter(
            timestamp__gte=thirty_days_ago
        ).values('session_id').distinct().count()
        
        # Count unique buyers in last 30 days
        buyers_30d = Ticket.objects.filter(
            purchased_at__gte=thirty_days_ago
        ).values('buyer_email').distinct().count()
        
        conversion_rate = (buyers_30d / unique_visitors * 100) if unique_visitors > 0 else 0
    except Exception:
        total_visits = 0
        unique_visitors = 0
        conversion_rate = 0
    
    # ═══════════════════════════════════════════════════════════════
    # NEW METRIC 3: ACTIVE USERS (30 DAYS)
    # ═══════════════════════════════════════════════════════════════
    # Users who logged in or made a purchase in last 30 days
    active_users_30d = User.objects.filter(
        Q(last_login__gte=thirty_days_ago) |
        Q(purchased_tickets__purchased_at__gte=thirty_days_ago)
    ).distinct().count()
    
    active_users_percent = (active_users_30d / total_users * 100) if total_users > 0 else 0
    
    # ═══════════════════════════════════════════════════════════════
    # NEW METRIC 4: REVENUE GROWTH (Month over Month)
    # ═══════════════════════════════════════════════════════════════
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_revenue = Ticket.objects.filter(
        purchased_at__gte=current_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    last_month_revenue = Ticket.objects.filter(
        purchased_at__gte=last_month_start,
        purchased_at__lt=current_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    if last_month_revenue > 0:
        revenue_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100)
        revenue_growth = float(revenue_growth)
    else:
        revenue_growth = 0 if current_month_revenue == 0 else 100
    
    # ═══════════════════════════════════════════════════════════════
    # NEW METRIC 5: REPEAT BUYERS
    # ═══════════════════════════════════════════════════════════════
    # Users who bought more than once
    repeat_buyers = Ticket.objects.values('buyer_email').annotate(
        purchase_count=Count('id')
    ).filter(purchase_count__gt=1).count()
    
    total_buyers = Ticket.objects.values('buyer_email').distinct().count()
    repeat_buyer_rate = (repeat_buyers / total_buyers * 100) if total_buyers > 0 else 0
    
    # ═══════════════════════════════════════════════════════════════
    # CHARTS DATA
    # ═══════════════════════════════════════════════════════════════
    
    # Recent activity
    recent_tickets = Ticket.objects.select_related(
        'event', 'ticket_category', 'buyer'
    ).order_by('-purchased_at')[:10]
    
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # User signup trend WITH BUYER/SELLER DISTINCTION
    user_signup_trend = list(User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).extra({
        'signup_date': "date(date_joined)"
    }).values('signup_date').annotate(
        count=Count('id'),
        buyers=Count('id', filter=Q(is_buyer=True)),
        sellers=Count('id', filter=Q(is_seller=True))
    ).order_by('signup_date'))
    
    # Daily sales
    daily_sales = list(Ticket.objects.filter(
        purchased_at__gte=thirty_days_ago
    ).values('purchased_at__date').annotate(
        total_sales=Sum('total_amount'),
        count=Count('id')
    ).order_by('purchased_at__date'))
    
    for sale in daily_sales:
        if sale['purchased_at__date']:
            sale['purchased_at__date'] = sale['purchased_at__date'].isoformat()
    
    # Tier breakdown
    tier_breakdown = list(TicketCategory.objects.values('name').annotate(
        sold=Count('tickets', filter=Q(tickets__status='confirmed')),
    ).filter(sold__gt=0).order_by('-sold'))
    
    # ═══════════════════════════════════════════════════════════════
    # CONTEXT
    # ═══════════════════════════════════════════════════════════════
    
    context = {
        # Existing metrics
        'total_users': total_users,
        'new_users_week': new_users_week,
        'active_users_count': active_users,
        'total_tickets': total_tickets,
        'tickets_today': tickets_today,
        'total_revenue': total_revenue,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'mpesa_success_rate': mpesa_success_rate,
        'mpesa_total_attempts': mpesa_total_attempts,
        'avg_ticket_price': avg_ticket_price,
        'tickets_this_week': tickets_this_week,
        
        # NEW METRICS
        'active_sellers': active_sellers,
        'conversion_rate': round(conversion_rate, 1),
        'total_visits': total_visits,
        'unique_visitors': unique_visitors,
        'active_users_30d': active_users_30d,
        'active_users_percent': round(active_users_percent, 1),
        'revenue_growth': round(revenue_growth, 1),
        'repeat_buyers': repeat_buyers,
        'repeat_buyer_rate': round(repeat_buyer_rate, 1),
        
        # Charts
        'recent_tickets': recent_tickets,
        'recent_users': recent_users,
        'user_signup_trend': json.dumps(user_signup_trend, cls=DjangoJSONEncoder),
        'daily_sales': json.dumps(daily_sales, cls=DjangoJSONEncoder),
        'tier_breakdown_json': json.dumps(tier_breakdown, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'admin/dashboard.html', context)


# ============================================================================
# USER PROFILE MANAGEMENT
# ============================================================================

@login_required
def profile_view(request):
    """View user profile based on their role - FIXED STATS"""
    user = request.user
    now = timezone.now()
    
    # Build filter for tickets (same as my_tickets view)
    ticket_filter = Q(buyer=user)
    
    if user.email:
        ticket_filter |= Q(buyer_email=user.email)
    
    if hasattr(user, 'phone_number') and user.phone_number:
        phone = user.phone_number.replace('+', '').replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        ticket_filter |= Q(buyer_phone=phone)
        ticket_filter |= Q(buyer_phone=user.phone_number)
    
    # Get tickets using same filter as my_tickets
    all_tickets = Ticket.objects.filter(ticket_filter)
    
    context = {'user': user}
    
    if user.is_seller:
        active_events_count = user.events.filter(is_active=True).count()
        context.update({
            'active_events_count': active_events_count,
            'total_events': user.events.count(),
            'tickets_sold': 0,
            'total_revenue': 0
        })
        return render(request, 'profile/seller_profile.html', context)
    elif user.is_buyer:
        # Use correct ticket counts that match my_tickets page
        context.update({
            'total_tickets': all_tickets.count(),
            'confirmed_tickets': all_tickets.filter(status='confirmed').count(),
            'used_tickets': all_tickets.filter(status='used').count()
        })
        return render(request, 'profile/buyer_profile.html', context)
    else:
        return render(request, 'profile/default_profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile based on their role"""
    if request.user.is_seller:
        form_class = SellerProfileForm
        template_name = 'profile/seller_profile_edit.html'
        success_message = 'Seller profile updated successfully!'
    elif request.user.is_buyer:
        form_class = BuyerProfileForm
        template_name = 'profile/buyer_profile_edit.html'
        success_message = 'Buyer profile updated successfully!'
    else:
        form_class = BuyerProfileForm
        template_name = 'profile/buyer_profile_edit.html'
        success_message = 'Profile updated successfully!'
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('profile_view')
    else:
        form = form_class(instance=request.user)
    
    return render(request, template_name, {'form': form})


@login_required
def profile_delete(request):
    """Delete user profile with confirmation"""
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    return render(request, 'profile/confirm_delete.html')


# ============================================================================
# BUYER TICKET & ORDER VIEWS
# ============================================================================

@login_required
def my_tickets(request):
    """View all tickets purchased by the logged-in user"""
    user = request.user
    now = timezone.now()
    
    # Build filter: match by user FK OR email OR phone
    ticket_filter = Q(buyer=user)
    
    if user.email:
        ticket_filter |= Q(buyer_email=user.email)
    
    if hasattr(user, 'phone_number') and user.phone_number:
        phone = user.phone_number.replace('+', '').replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        ticket_filter |= Q(buyer_phone=phone)
        ticket_filter |= Q(buyer_phone=user.phone_number)
    
    upcoming_tickets = Ticket.objects.select_related(
        'event', 'ticket_category'
    ).filter(
        ticket_filter,
        event__date__gte=now
    ).order_by('event__date')
    
    past_tickets = Ticket.objects.select_related(
        'event', 'ticket_category'
    ).filter(
        ticket_filter,
        event__date__lt=now
    ).order_by('-event__date')
    
    context = {
        'upcoming_tickets': upcoming_tickets,
        'past_tickets': past_tickets,
    }
    return render(request, 'profile/my_tickets.html', context)


@login_required
def buyer_merchandise_order_list(request):
    """View all merchandise orders for the logged-in buyer"""
    if not request.user.is_buyer:
        messages.warning(request, 'This page is only available to buyers.')
        return redirect('profile_view')
    
    try:
        from .models_merchandise import MerchandiseOrder, OrderItem
        
        orders = MerchandiseOrder.objects.filter(buyer=request.user)\
            .prefetch_related('items__merchandise')\
            .order_by('-created_at')
        
        pending_orders_count = orders.filter(status='pending').count()
        shipped_orders_count = orders.filter(status='shipped').count()
        delivered_orders_count = orders.filter(status='delivered').count()
        
        context = {
            'orders': orders,
            'pending_orders_count': pending_orders_count,
            'shipped_orders_count': shipped_orders_count,
            'delivered_orders_count': delivered_orders_count,
        }
        return render(request, 'merchandise/buyer_order_list.html', context)
    except ImportError:
        messages.info(request, 'Merchandise feature not available yet.')
        return redirect('profile_view')


@login_required
def buyer_merchandise_order_detail(request, pk):
    """View details of a specific merchandise order"""
    if not request.user.is_buyer:
        messages.warning(request, 'This page is only available to buyers.')
        return redirect('profile_view')
    
    try:
        from .models_merchandise import MerchandiseOrder, OrderItem
        
        order = get_object_or_404(MerchandiseOrder, pk=pk, buyer=request.user)
        order_items = order.orderitem_set.select_related('merchandise').all()
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'merchandise/buyer_order_detail.html', context)
    except ImportError:
        messages.info(request, 'Merchandise feature not available yet.')
        return redirect('profile_view')


# ============================================================================
# M-PESA PAYMENT SUCCESS (Placeholder)
# ============================================================================

def payment_success(request):
    """M-Pesa payment success handler - TO BE IMPLEMENTED"""
    messages.success(request, 'Payment successful! Your tickets will be sent to your email.')
    return redirect('my_tickets')


# ============================================================================
# HEALTH CHECK (for UptimeRobot)
# ============================================================================

def health_check(request):
    """Lightweight health check endpoint for monitoring services"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'zozaprime'
    })
    

@require_GET
@cache_control(max_age=3600)
def service_worker(request):
    """Serve the service worker JavaScript file"""
    sw_content = render_to_string('events/sw.js')
    return HttpResponse(sw_content, content_type='application/javascript')