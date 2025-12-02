from django.contrib import admin
from django.contrib.auth.models import Permission
from . models import Customer,Order,OrderItem,Product,Category,ShippingAdderss,Wishlist,ContactMessage,ProductImage


# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    list_display_links = ['name']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def product_count(self, obj):
        """Display number of products in this category"""
        return obj.products.count()
    product_count.short_description = 'Products'
    
    def created_at(self, obj):
        """Display when category was created"""
        if hasattr(obj, 'created'):
            return obj.created
        return '-'
    created_at.short_description = 'Created'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug':('name',)}
    inlines = [ProductImageInline]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
    list_filter = []
    search_fields = ['name', 'email']
    ordering = ['name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status', 'date_odered', 'last_updated', 'get_cart_total']
    list_filter = ['status', 'date_odered', 'last_updated']
    search_fields = ['custamer__name', 'custamer__email', 'tracking_number']
    ordering = ['-date_odered']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'date_added', 'line_total']
    list_filter = ['date_added']
    search_fields = ['order__custamer__name', 'product__name']
    ordering = ['-date_added']

    def unit_price(self, obj):
        if obj.product and hasattr(obj.product, 'price') and obj.product.price is not None:
            return obj.product.price
        return obj.product_price

@admin.register(ShippingAdderss)
class ShippingAdderssAdmin(admin.ModelAdmin):
    list_display = ['order', 'custamer', 'address', 'city', 'state', 'zipcode', 'date_added']
    list_filter = ['date_added']
    search_fields = ['order__custamer__name', 'custamer__name', 'address', 'city', 'state', 'zipcode']
    ordering = ['-date_added']

admin.site.register(Permission)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']                                                                                                                                                                                                                                                                                                
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']