from django.db import models
from store.models import Order

# Create your models here.

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=[('Percentage', 'Percentage'),('Fixed', 'Fixed Amount')])
    value = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=0)


class OrderCoupon(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)