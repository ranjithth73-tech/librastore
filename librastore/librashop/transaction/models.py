from django.db import models
from store.models import Order, OrderItem

# Create your models here.

class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending...')
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    