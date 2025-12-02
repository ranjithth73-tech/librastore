from django import forms
from . models import ShippingAdderss

class ShippingAdderssForm(forms.ModelForm):
    class Meta:
        model = ShippingAdderss
        fields = ['address', 'city', 'state', 'zipcode']
        