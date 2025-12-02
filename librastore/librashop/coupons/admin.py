from django.contrib import admin
from django.utils import timezone
from . models import Coupon, OrderCoupon

# Register your models here.

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_badge', 'discount_type', 'value', 'validity_status', 'usage_count', 'active']
    list_filter = ['active', 'discount_type', 'valid_from', 'valid_to']
    search_fields = ['code']
    ordering = ['-valid_from']
    list_editable = ['active']
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'discount_type', 'value')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Settings', {
            'fields': ('active', 'max_users')
        }),
    )
    
    def discount_badge(self, obj):
        """Display discount in a readable format"""
        if obj.discount_type == 'Percentage':
            return f"🏷️ {obj.value}% OFF"
        else:
            return f"💰 ₹{obj.value} OFF"
    discount_badge.short_description = 'Discount'
    
    def validity_status(self, obj):
        """Show if coupon is currently valid"""
        now = timezone.now()
        if obj.valid_from <= now <= obj.valid_to:
            return "✅ Active Now"
        elif now < obj.valid_from:
            return "⏳ Upcoming"
        else:
            return "❌ Expired"
    validity_status.short_description = 'Status'
    
    def usage_count(self, obj):
        """Show how many times coupon was used"""
        count = obj.ordercoupon_set.count()
        if obj.max_users > 0:
            return f"{count} / {obj.max_users}"
        return f"{count} / ∞"
    usage_count.short_description = 'Usage'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(OrderCoupon)
class OrderCouponAdmin(admin.ModelAdmin):
    list_display = ['order', 'coupon', 'discount_amount', 'applied_date']
    list_filter = ['coupon']
    search_fields = ['order__id', 'coupon__code']
    readonly_fields = ['order', 'coupon', 'discount_amount']
    
    def applied_date(self, obj):
        """Show when coupon was applied"""
        if hasattr(obj.order, 'date_odered'):
            return obj.order.date_odered
        return '-'
    applied_date.short_description = 'Applied On'
    