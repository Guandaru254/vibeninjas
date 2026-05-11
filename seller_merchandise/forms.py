from django import forms
from .models import SellerMerchandise, SellerMerchandiseCategory, SellerMerchandiseOrder
from django.forms import ModelForm, Textarea, NumberInput, Select, FileInput, TextInput

class SellerMerchandiseForm(forms.ModelForm):
    class Meta:
        model = SellerMerchandise
        fields = ['name', 'description', 'price', 'stock_quantity', 'category', 'image', 'is_featured']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'description': Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Enter product description'
            }),
            'price': NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'stock_quantity': NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'category': Select(attrs={'class': 'form-select'}),
            'image': FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'image': 'Upload a high-quality image of your product (max 5MB)',
            'price': 'Price in Kenyan Shillings (KSh)',
            'is_featured': 'Mark this item as featured to highlight it on your event page',
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store user for event filtering in view
        self.user = user

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is not None and stock_quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock_quantity

class SellerMerchandiseOrderForm(forms.Form):
    """
    A form for creating seller merchandise orders.
    """
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'value': '1',
            'id': 'id_quantity',
        }),
        help_text='Enter quantity you wish to order',
        required=True
    )
    
    # Shipping Information Fields
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        }),
        required=True
    )
    
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        }),
        required=True
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
        }),
        required=True
    )
    
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '7XX XXX XXX',
        }),
        required=True
    )
    
    address_line1 = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street address',
        }),
        required=True
    )
    
    address_line2 = forms.CharField(
        required=False,
        max_length=255,
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apartment, suite, etc. (optional)',
        })
    )
    
    city = forms.CharField(
        max_length=100,
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City',
            'required': True,
        })
    )
    
    county = forms.CharField(
        max_length=100,
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'County',
            'required': True,
        })
    )
    
    postal_code = forms.CharField(
        required=False,
        max_length=20,
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal code (optional)',
        })
    )
    
    country = forms.CharField(
        max_length=100,
        initial='Kenya',
        widget=TextInput(attrs={
            'class': 'form-control',
            'required': True,
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=(
            ('mpesa', 'M-Pesa'),
            ('card', 'Credit/Debit Card'),
            ('pay_on_delivery', 'Pay on Delivery')
        ),
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        initial='mpesa',
        required=True
    )
    
    notes = forms.CharField(
        required=False,
        widget=Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any special instructions for delivery',
        })
    )

    def __init__(self, *args, **kwargs):
        self.merchandise = kwargs.pop('merchandise', None)
        super().__init__(*args, **kwargs)
        
        if self.merchandise:
            self.fields['quantity'].widget.attrs['max'] = self.merchandise.stock_quantity
            self.fields['quantity'].help_text = f'Maximum available: {self.merchandise.stock_quantity}'

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        
        if self.merchandise and quantity > self.merchandise.stock_quantity:
            raise forms.ValidationError(
                f'Only {self.merchandise.stock_quantity} items available in stock.'
            )
        
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
            
        return quantity

class SellerMerchandiseCategoryForm(forms.ModelForm):
    class Meta:
        model = SellerMerchandiseCategory
        fields = ['name', 'description']
        widgets = {
            'name': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name',
            }),
            'description': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this category',
            }),
        }
        help_texts = {
            'name': 'A short, descriptive name for category',
            'description': 'Optional description to help users understand what items belong in this category',
        }
