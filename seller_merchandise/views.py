from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from .models import SellerMerchandise, SellerMerchandiseCategory, SellerMerchandiseOrder, SellerOrderItem
from .forms import SellerMerchandiseForm, SellerMerchandiseOrderForm, SellerMerchandiseCategoryForm

# Seller Merchandise Views
@login_required
def seller_merchandise_dashboard(request):
    """Main dashboard for sellers to manage their merchandise"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Only sellers can access this dashboard
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can access the merchandise dashboard.')
        return redirect('home')
    
    # Get seller's merchandise
    merchandise = SellerMerchandise.objects.filter(seller=request.user)
    
    # Get seller's orders
    orders = SellerMerchandiseOrder.objects.filter(seller=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_products = merchandise.count()
    active_products = merchandise.filter(status='active').count()
    total_sales = orders.count()
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get recent orders (last 5)
    recent_orders = orders[:5]
    
    # Get low stock items (less than 5 in stock)
    low_stock_items = merchandise.filter(stock_quantity__lt=5, stock_quantity__gt=0)
    out_of_stock_items = merchandise.filter(stock_quantity=0)
    
    context = {
        'merchandise': merchandise,
        'orders': recent_orders,
        'total_products': total_products,
        'active_products': active_products,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    
    return render(request, 'seller_merchandise/dashboard.html', context)

class SellerMerchandiseListView(LoginRequiredMixin, ListView):
    """List view for seller's merchandise"""
    model = SellerMerchandise
    template_name = 'seller_merchandise/list.html'
    context_object_name = 'merchandise_list'
    paginate_by = 12
    
    def dispatch(self, request, *args, **kwargs):
        # Only sellers can access this view
        if not request.user.is_seller:
            messages.error(request, 'Only sellers can manage merchandise.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = SellerMerchandise.objects.filter(seller=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SellerMerchandiseCategory.objects.all()
        context['status_choices'] = SellerMerchandise.STATUS_CHOICES
        return context

class SellerMerchandiseDetailView(LoginRequiredMixin, DetailView):
    """Detail view for seller's merchandise"""
    model = SellerMerchandise
    template_name = 'seller_merchandise/detail.html'
    context_object_name = 'item'
    
    def get_queryset(self):
        return SellerMerchandise.objects.filter(seller=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get orders for this specific merchandise item
        context['orders'] = SellerMerchandiseOrder.objects.filter(
            items=self.object
        ).order_by('-created_at')[:10]
        return context

class SellerMerchandiseCreateView(LoginRequiredMixin, CreateView):
    """Create view for new merchandise"""
    model = SellerMerchandise
    form_class = SellerMerchandiseForm
    template_name = 'seller_merchandise/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only sellers can create merchandise
        if not request.user.is_seller:
            messages.error(request, 'Only sellers can add merchandise.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        # Handle event selection if provided
        if hasattr(form, 'cleaned_data') and 'event' in form.cleaned_data:
            form.instance.event = form.cleaned_data['event']
        messages.success(self.request, 'Your merchandise has been added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Merchandise'
        context['action'] = 'Add'
        return context

class SellerMerchandiseUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for merchandise"""
    model = SellerMerchandise
    form_class = SellerMerchandiseForm
    template_name = 'seller_merchandise/form.html'
    
    def get_queryset(self):
        return SellerMerchandise.objects.filter(seller=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Merchandise updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Merchandise'
        context['action'] = 'Update'
        return context

class SellerMerchandiseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for merchandise"""
    model = SellerMerchandise
    template_name = 'seller_merchandise/confirm_delete.html'
    success_url = reverse_lazy('seller_merchandise_list')
    
    def get_queryset(self):
        return SellerMerchandise.objects.filter(seller=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Merchandise has been deleted.')
        return super().delete(request, *args, **kwargs)

# Public Merchandise Views (for buyers)
class PublicMerchandiseListView(ListView):
    """Public list view for all available merchandise - accessible to buyers"""
    model = SellerMerchandise
    template_name = 'seller_merchandise/public_list.html'
    context_object_name = 'merchandise_list'
    paginate_by = 12
    
    def get_queryset(self):
        # Only show active merchandise from all sellers
        queryset = SellerMerchandise.objects.filter(
            status='active',
            stock_quantity__gt=0
        ).select_related('seller', 'category')
        
        # Filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        return queryset.order_by('-is_featured', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SellerMerchandiseCategory.objects.all()
        return context

class PublicMerchandiseDetailView(DetailView):
    """Public detail view for merchandise - accessible to buyers"""
    model = SellerMerchandise
    template_name = 'seller_merchandise/public_detail.html'
    context_object_name = 'item'
    
    def get_queryset(self):
        # Only show active merchandise
        return SellerMerchandise.objects.filter(
            status='active',
            stock_quantity__gt=0
        ).select_related('seller', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get other merchandise from the same seller
        context['related_items'] = SellerMerchandise.objects.filter(
            seller=self.object.seller,
            status='active',
            stock_quantity__gt=0
        ).exclude(pk=self.object.pk)[:4]
        return context

# Order Views
@login_required
def create_seller_merchandise_order(request, item_id):
    """Create an order for seller merchandise"""
    item = get_object_or_404(SellerMerchandise, id=item_id, status='active')
    
    # Only buyers can purchase merchandise (sellers can't buy their own or others' merchandise)
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers can purchase merchandise.')
        return redirect('public_merchandise_detail', pk=item_id)
    
    # Prevent sellers from buying their own merchandise
    if request.user == item.seller:
        messages.error(request, 'You cannot purchase your own merchandise.')
        return redirect('public_merchandise_detail', pk=item_id)
    
    # Initialize form with user data if available
    initial_data = {}
    if request.user.is_authenticated:
        initial_data.update({
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone_number': getattr(request.user, 'phone_number', ''),
        })
    
    if request.method == 'POST':
        form = SellerMerchandiseOrderForm(request.POST, merchandise=item)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Combine shipping information into a single string
                    shipping_parts = [
                        f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                        form.cleaned_data['email'],
                        form.cleaned_data['phone_number'],
                        form.cleaned_data['address_line1'],
                    ]
                    
                    # Add optional address line 2 if it exists
                    if form.cleaned_data.get('address_line2'):
                        shipping_parts.append(form.cleaned_data['address_line2'])
                    
                    # Add city, county, postal code, and country
                    shipping_parts.extend([
                        form.cleaned_data['city'],
                        form.cleaned_data['county'],
                    ])
                    
                    if form.cleaned_data.get('postal_code'):
                        shipping_parts.append(f"Postal Code: {form.cleaned_data['postal_code']}")
                    
                    shipping_parts.append(form.cleaned_data['country'])
                    
                    # Create order with shipping information
                    order = SellerMerchandiseOrder.objects.create(
                        buyer=request.user,
                        seller=item.seller,
                        total_amount=item.price * form.cleaned_data['quantity'],
                        status='pending',
                        payment_method=form.cleaned_data.get('payment_method', 'mpesa'),
                        shipping_address='\n'.join(shipping_parts),
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Create order item
                    SellerOrderItem.objects.create(
                        order=order,
                        merchandise=item,
                        quantity=form.cleaned_data['quantity'],
                        price=item.price
                    )
                    
                    # Update stock
                    item.stock_quantity -= form.cleaned_data['quantity']
                    if item.stock_quantity <= 0:
                        item.status = 'sold_out'
                    item.save()
                    
                    messages.success(request, 'Your order has been placed successfully!')
                    return redirect('seller_merchandise_order_detail', pk=order.id)
                    
            except Exception as e:
                messages.error(request, f'An error occurred while processing your order. Please try again.')
        else:
            # Form is not valid, show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
                    
        # If we get here, there was an error - render form again with errors
        return render(request, 'seller_merchandise/order_form.html', {
            'form': form,
            'item': item
        })
    else:
        form = SellerMerchandiseOrderForm(initial=initial_data, merchandise=item)
    
    return render(request, 'seller_merchandise/order_form.html', {
        'form': form,
        'item': item
    })

@login_required
def seller_merchandise_order_detail(request, pk):
    """View order details"""
    order = get_object_or_404(SellerMerchandiseOrder, pk=pk)
    
    # Check if user is either buyer or seller
    if not (order.buyer == request.user or order.seller == request.user):
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('home')
    
    return render(request, 'seller_merchandise/order_detail.html', {'order': order})

@login_required
def seller_merchandise_order_list(request):
    """List orders for the seller"""
    orders = SellerMerchandiseOrder.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'seller_merchandise/order_list.html', {'orders': orders})

# Category Management
class SellerMerchandiseCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create view for merchandise categories"""
    model = SellerMerchandiseCategory
    form_class = SellerMerchandiseCategoryForm
    template_name = 'seller_merchandise/category_form.html'
    success_url = reverse_lazy('seller_merchandise_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Category'
        return context
