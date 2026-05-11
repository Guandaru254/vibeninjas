from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import User, Event, Category, TicketCategory


class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = [
            'name',
            'category_type',
            'price',
            'available_tickets',
            'description',
            'max_tickets_per_purchase',
            'sales_start',
            'sales_end',
            'is_free',
            'is_bundle',
            'bundle_size',
            'bundle_label',
            'display_order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. General, VIP, Couples Pass'
            }),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0 for free'
            }),
            'available_tickets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': "What's included, perks, restrictions..."
            }),
            'max_tickets_per_purchase': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'sales_start': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'sales_end': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bundle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bundle_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20',
            }),
            'bundle_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "e.g. Admits 2, Table of 8"
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price') or 0
        is_free = cleaned_data.get('is_free', False)
        is_bundle = cleaned_data.get('is_bundle', False)
        bundle_size = cleaned_data.get('bundle_size') or 1

        if is_free or price == 0:
            cleaned_data['price'] = 0
            cleaned_data['is_free'] = True

        if is_bundle and bundle_size < 2:
            cleaned_data['bundle_size'] = 2

        if is_bundle:
            if bundle_size == 2:
                cleaned_data['category_type'] = 'couples'
            elif bundle_size >= 3:
                cleaned_data['category_type'] = 'group'

        return cleaned_data


TicketCategoryFormSet = inlineformset_factory(
    Event,
    TicketCategory,
    form=TicketCategoryForm,
    extra=1,
    max_num=8,
    can_delete=True
)


class EventForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].widget.attrs['value'] = self.instance.date.strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'image', 'date', 'location', 'total_tickets']
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'total_tickets': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        return super().clean()


class TicketPurchaseForm(forms.Form):
    buyer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    buyer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    buyer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def clean(self):
        return super().clean()


class BuyerSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.is_buyer = True
        user.is_seller = False
        if commit:
            user.save()
        return user


class SellerSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    business_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    business_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "business_name",
                  "business_description", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.business_name = self.cleaned_data['business_name']
        user.business_description = self.cleaned_data['business_description']
        user.is_seller = True
        user.is_buyer = False
        if commit:
            user.save()
        return user


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture',
                  'business_name', 'business_description']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }