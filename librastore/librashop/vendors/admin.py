from django.contrib import admin
from . models import Vendor

# Register your models here.

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'owner_name', 'phone']
    prepopulated_fields = {'slug':('store_name',)}