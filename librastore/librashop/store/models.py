from django.db import models
from django.contrib.auth.models import User
from vendors . models import Vendor
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    hero_video = models.FileField(upload_to='videos/categories/', blank=True, null=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

        def __str__(self):
            return self.name 

class Product(models.Model):
    category = models.ForeignKey('store.Category', related_name='products', on_delete=models.CASCADE)
    vendor = models.ForeignKey('vendors.Vendor', related_name='products', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=199, db_index=True)
    slug = models.SlugField(max_length=199, db_index=True)
    image = models.ImageField(upload_to='products/%y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%y/%m/%d/gallery')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - image {self.id}"







class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Order(models.Model):
    custamer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_odered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], 
        default='pending'
    )
    # Tracking fields
    TRACKING_STAGE_CHOICES = [
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'), 
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    carrier = models.CharField(max_length=100, null=True, blank=True)
    tracking_stage = models.CharField(max_length=32, choices=TRACKING_STAGE_CHOICES, default='placed')
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) 
    
    # --- Compatibility helpers (non-breaking) ---
    @property
    def date(self):
        """Alias for date_odered (legacy typo)."""
        return self.date_odered

    @property
    def customer(self):
        """Alias for custamer (legacy typo)."""
        return self.custamer

    @property
    def get_cart_total(self):
        """Sum of all order item line totals."""
        items = self.orderitem_set.all()
        return sum([(item.line_total or 0) for item in items])

    @property
    def get_cart_items(self):
        """Total quantity of items in the order."""
        items = self.orderitem_set.all()
        return sum([(item.quantity or 0) for item in items])
    

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    # Snapshot fields to preserve product details at time of order
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    product_image = models.CharField(max_length=500, null=True, blank=True)

    @property
    def line_total(self):
        """Return total price for this item (quantity * unit price)."""
        try:
            unit_price = None
            if self.product and hasattr(self.product, 'price') and self.product.price is not None:
                unit_price = self.product.price
            elif self.product_price is not None:
                unit_price = self.product_price
            else:
                unit_price = 0
            return (self.quantity or 0) * unit_price
        except Exception:
            return 0

    # Backwards-compatible alias used in some templates/code
    @property
    def get_total(self):
        return self.line_total
        

class ShippingAdderss(models.Model):
    custamer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False)
    zipcode = models.CharField(max_length=200, null=False)
    date_added = models.DateField(auto_now_add=True)



    def __str__(self):
        return self.address


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"

