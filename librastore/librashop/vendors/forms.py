from django import forms
from store.models import Product
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import Vendor
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price']

User = get_user_model()

class CombinedRegistrationForm(UserCreationForm):
    store_name = forms.CharField(max_length=200)
    owner_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea)
    logo = forms.ImageField(required=False)

    email = forms.EmailField(
        required=True,
        help_text="Required. Add a valid email address.",
        widget=forms.EmailInput
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email'] + list(UserCreationForm.Meta.fields)




    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email
    



    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_vendor = True
        user.save()

        Vendor.objects.create(
            user=user,
            store_name=self.cleaned_data['store_name'],
            owner_name=self.cleaned_data['owner_name'],
            phone=self.cleaned_data['phone'],
            address=self.cleaned_data['address'],
            logo=self.cleaned_data['logo']
        )
        return user


class VendorSettingsForm(forms.ModelForm):
    """Form for vendors to update their profile settings"""
    class Meta:
        model = Vendor
        fields = ['store_name', 'owner_name', 'phone', 'address', 'logo']
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your store name'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter owner name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your store address',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }