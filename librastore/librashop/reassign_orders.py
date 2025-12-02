#!/usr/bin/env python
"""
Reassign orders to the correct user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librashop.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Customer, Order

User = get_user_model()

print("=" * 60)
print("REASSIGNING ORDERS")
print("=" * 60)

# Show all users
print("\nAvailable users:")
for i, u in enumerate(User.objects.all(), 1):
    customer = Customer.objects.filter(user=u).first()
    order_count = Order.objects.filter(custamer=customer).count() if customer else 0
    print(f"{i}. {u.username} (email: {u.email}, orders: {order_count})")

# The most recently logged in user is likely the one who placed the order
recent_user = User.objects.filter(last_login__isnull=False).order_by('-last_login').first()
if recent_user:
    print(f"\nMost recently active user: {recent_user.username} (last login: {recent_user.last_login})")
else:
    print("\nMost recently active user: None")

def ensure_customer(user):
    if user is None:
        return None, None
    customer, _ = Customer.objects.get_or_create(
        user=user,
        defaults={
            'name': user.get_full_name() or user.username,
            'email': user.email or 'no-email@example.com'
        }
    )
    return customer, _

# Source (from) and target (to) usernames
FROM_USERNAME = os.environ.get('FROM_USERNAME', 'rishad')
TO_USERNAME = os.environ.get('TO_USERNAME', 'user1')

try:
    rishad_user = User.objects.get(username=FROM_USERNAME)
except User.DoesNotExist:
    print(f"\nERROR: Source user '{FROM_USERNAME}' not found. Set FROM_USERNAME env or adjust script.")
    raise SystemExit(1)

rishad_customer = Customer.objects.filter(user=rishad_user).first()
if not rishad_customer:
    rishad_customer, _ = Customer.objects.get_or_create(
        user=rishad_user,
        defaults={'name': rishad_user.get_full_name() or rishad_user.username, 'email': rishad_user.email or 'no-email@example.com'}
    )

try:
    target_user = User.objects.get(username=TO_USERNAME)
except User.DoesNotExist:
    print(f"\nERROR: Target user '{TO_USERNAME}' not found. Set TO_USERNAME env or adjust script.")
    raise SystemExit(1)

target_customer, _ = Customer.objects.get_or_create(
    user=target_user,
    defaults={
        'name': target_user.get_full_name() or target_user.username,
        'email': target_user.email or 'no-email@example.com'
    }
)

print(f"\nReassigning orders from {rishad_user.username} to {target_user.username}...")

# Move orders from rishad to user1
orders_to_move = Order.objects.filter(custamer=rishad_customer)
count = orders_to_move.count()
orders_to_move.update(custamer=target_customer)

print(f"✓ Moved {count} orders")
print(f"\n{target_user.username} now has {Order.objects.filter(custamer=target_customer).count()} orders")
print(f"{rishad_user.username} now has {Order.objects.filter(custamer=rishad_customer).count()} orders")

print("\n" + "=" * 60)
