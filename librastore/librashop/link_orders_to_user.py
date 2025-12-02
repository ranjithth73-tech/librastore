#!/usr/bin/env python
"""
Link orphan orders to the correct user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librashop.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Customer, Order

User = get_user_model()

print("=" * 60)
print("LINKING ORPHAN ORDERS TO USERS")
print("=" * 60)

# Get the ranjith@gmail.com user
user = User.objects.filter(email__icontains='ranjith').first()
if not user:
    # Try finding by username containing ranjith
    user = User.objects.filter(username__icontains='ranjith').first()

if user:
    print(f"\nFound user: {user.username} (email: {user.email})")
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={
            'name': user.get_full_name() or user.username,
            'email': user.email or 'no-email@example.com'
        }
    )
    print(f"Customer: {customer.name}")
    
    # Link all orphan orders to this customer
    orphan_orders = Order.objects.filter(custamer__isnull=True)
    count = orphan_orders.count()
    
    if count > 0:
        print(f"\nLinking {count} orphan orders to {customer.name}...")
        orphan_orders.update(custamer=customer)
        print(f"✓ Successfully linked {count} orders!")
    else:
        print("\n✓ No orphan orders found")
    
    # Show summary
    print(f"\n{user.username} now has {Order.objects.filter(custamer=customer).count()} orders")
    
else:
    print("\nNo user found with 'ranjith' in username or email")
    print("\nAll users:")
    for u in User.objects.all():
        print(f"  - {u.username} (email: {u.email})")

print("\n" + "=" * 60)
