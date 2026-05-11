from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Merchandise, MerchandiseCategory, MerchandiseOrder, OrderItem
from .forms_merchandise import MerchandiseForm, MerchandiseOrderForm

# Merchandise Views
class MerchandiseListView(ListView):
    model = Merchandise
    template_name = 'merchandise/list.html'
    context_object_name = 'merchandise_list'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Merchandise.objects.filter(status='active', stock_quantity__gt=0)
        
        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Sort by price, newest, etc.
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        else:  # newest first by default
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MerchandiseCategory.objects.all()
        return context

class MerchandiseDetailView(DetailView):
    model = Merchandise
    template_name = 'merchandise/detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_items'] = Merchandise.objects.filter(
            category=self.object.category,
            status='active',
            stock_quantity__gt=0
        ).exclude(id=self.object.id)[:4]
        return context

class MerchandiseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Merchandise
    form_class = MerchandiseForm
    template_name = 'merchandise/form.html'
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        form.instance.seller_type = 'seller' if self.request.user.is_seller else 'admin'
        messages.success(self.request, 'Your merchandise has been listed successfully!')
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_seller or self.request.user.is_staff)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Merchandise'
        return context

class MerchandiseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Merchandise
    form_class = MerchandiseForm
    template_name = 'merchandise/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Merchandise updated successfully!')
        return super().form_valid(form)
    
    def test_func(self):
        merchandise = self.get_object()
        return self.request.user == merchandise.seller or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Merchandise'
        return context

class MerchandiseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Merchandise
    template_name = 'merchandise/confirm_delete.html'
    success_url = reverse_lazy('merchandise_list')
    
    def test_func(self):
        merchandise = self.get_object()
        return self.request.user == merchandise.seller or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Merchandise has been deleted.')
        return super().delete(request, *args, **kwargs)

# Order Views
@login_required
def create_order(request, item_id):
    item = get_object_or_404(Merchandise, id=item_id, status='active')
    
    # Initialize form with user data if available
    initial_data = {}
    if request.user.is_authenticated:
        initial_data.update({
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone_number': request.user.phone_number or '',
        })
        
        # Try to get user's default shipping address if UserAddress model exists
        try:
            from django.apps import apps
            if apps.is_installed('events') and 'UserAddress' in [model.__name__ for model in apps.get_app_config('events').get_models()]:
                from .models import UserAddress
                try:
                    address = UserAddress.objects.get(user=request.user, is_default=True)
                    initial_data.update({
                        'address_line1': address.address_line1,
                        'address_line2': address.address_line2 or '',
                        'city': address.city,
                        'county': address.county,
                        'postal_code': address.postal_code or '',
                        'country': address.country,
                    })
                except UserAddress.DoesNotExist:
                    pass
        except (ImportError, LookupError):
            # If there's any error with the UserAddress model, just continue without it
            pass
    
    if request.method == 'POST':
        form = MerchandiseOrderForm(request.POST, merchandise=item)
        if form.is_valid():
            try:
                from django.db import transaction
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
                    
                    # Create the order with shipping information
                    order = MerchandiseOrder.objects.create(
                        buyer=request.user,
                        total_amount=item.price * form.cleaned_data['quantity'],
                        status='pending',
                        payment_method=form.cleaned_data.get('payment_method', 'mpesa'),
                        shipping_address='\n'.join(shipping_parts),
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Create order item
                    OrderItem.objects.create(
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
                    return redirect('merchandise_order_detail', pk=order.id)
                    
            except Exception as e:
                import traceback
                print("Error creating order:", str(e))
                print(traceback.format_exc())
                messages.error(request, f'An error occurred while processing your order. Please try again.')
        else:
            # Form is not valid, show form errors
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
                    
        # If we get here, there was an error - render the form again with errors
        return render(request, 'merchandise/order_form.html', {
            'form': form,
            'item': item
        })
    else:
        form = MerchandiseOrderForm(initial=initial_data, merchandise=item)
    
    return render(request, 'merchandise/order_form.html', {
        'form': form,
        'item': item
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(MerchandiseOrder, pk=pk, buyer=request.user)
    return render(request, 'merchandise/order_detail.html', {'order': order})

@login_required
def cancel_order(request, pk):
    """
    View to cancel an order.
    Only the buyer who placed the order can cancel it, and only if it's in a cancellable state.
    """
    order = get_object_or_404(MerchandiseOrder, pk=pk, buyer=request.user)
    
    # Check if the order can be cancelled (e.g., not already cancelled or shipped)
    if order.status not in ['pending', 'processing']:
        messages.error(request, 'This order cannot be cancelled at this stage.')
        return redirect('merchandise_order_detail', pk=order.pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update order status to cancelled
                order.status = 'cancelled'
                order.save()
                
                # Restock the items
                for item in order.orderitem_set.all():
                    item.merchandise.stock_quantity += item.quantity
                    item.merchandise.save()
                
                messages.success(request, 'Your order has been cancelled successfully.')
                return redirect('merchandise_order_detail', pk=order.pk)
                
        except Exception as e:
            messages.error(request, f'An error occurred while cancelling the order: {str(e)}')
            return redirect('merchandise_order_detail', pk=order.pk)
    
    # If not a POST request, show confirmation page
    return render(request, 'merchandise/order_cancel_confirm.html', {'order': order})

@login_required
def order_list(request):
    orders = MerchandiseOrder.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'merchandise/order_list.html', {'orders': orders})

@login_required
def order_payment(request, pk):
    """
    View to handle payment for an order.
    """
    order = get_object_or_404(MerchandiseOrder, id=pk, buyer=request.user)
    
    if order.paid:
        messages.info(request, 'This order has already been paid.')
        return redirect('merchandise_order_detail', pk=order.id)
        
    if order.status == 'cancelled':
        messages.error(request, 'This order has been cancelled and cannot be paid for.')
        return redirect('merchandise_order_detail', pk=order.id)
    
    # Here you would typically integrate with your payment gateway
    # For now, we'll just mark it as paid for demonstration purposes
    order.paid = True
    order.status = 'processing'  # Update status to processing after payment
    order.save()
    
    messages.success(request, 'Payment successful! Your order is now being processed.')
    return redirect('merchandise_order_detail', pk=order.id)

@login_required
def order_invoice(request, pk):
    """
    View to display an invoice for a specific order.
    """
    order = get_object_or_404(MerchandiseOrder, id=pk, buyer=request.user)
    
    # Check if the user is either the buyer or a staff member
    if not (order.buyer == request.user or request.user.is_staff):
        messages.error(request, 'You do not have permission to view this invoice.')
        return redirect('merchandise_order_detail', pk=order.id)
    
    # Calculate any additional details needed for the invoice
    context = {
        'order': order,
        'order_items': order.orderitem_set.all(),  # Using the default related name
        'now': timezone.now(),
        'company_name': 'TazamoEXP',
        'company_address': 'Kasarani, Nairobi, Kenya',
        'company_phone': '+254 111363870',  
        'company_email': 'info@tazamoafrica.com',  
    }
    
    return render(request, 'merchandise/order_invoice.html', context)

# Seller Dashboard Views
@login_required
def seller_dashboard(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'seller_profile'):
        return redirect('home')
        
    seller = request.user.seller_profile
    products = Merchandise.objects.filter(seller=seller)
    orders = MerchandiseOrder.objects.filter(
        order_items__merchandise__seller=seller
    ).distinct().order_by('-created_at')
    
    # Calculate total sales and revenue
    total_sales = orders.count()
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get recent orders (last 5)
    recent_orders = orders[:5]
    
    # Get low stock items (less than 5 in stock)
    low_stock_items = products.filter(stock_quantity__lt=5, stock_quantity__gt=0)
    out_of_stock_items = products.filter(stock_quantity=0)
    
    context = {
        'products': products,
        'orders': recent_orders,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    
    return render(request, 'merchandise/seller_dashboard.html', context)
