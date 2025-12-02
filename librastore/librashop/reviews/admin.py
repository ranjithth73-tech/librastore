from django.contrib import admin
from . models import Review

# Register your models here.

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating','created_at', 'is_approved']
    list_filter = ['is_approved', 'rating']
    list_editable = ['is_approved']
    search_fields = ['comment']
