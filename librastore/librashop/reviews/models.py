from django.db import models
from store.models import Product, Customer

# Create your models here.

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(choices=[(i,i) for i in range(1,6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

        
