#!/usr/bin/env python
"""
Fix orders that have no customer linked
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librashop.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Customer, Order, OrderItem
from cart.models import Cart

User = get_user_model()

print("=" * 60)
print("FIXING ORPHAN ORDERS")
print("=" * 60)

# Find all orders without a customer
orphan_orders = Order.objects.filter(custamer__isnull=True)
print(f"\nFound {orphan_orders.count()} orders without customers")

if orphan_orders.exists():
    print("\nThese orders need to be manually linked to customers.")
    print("Please identify which user these orders belong to:\n")
    
    for order in orphan_orders:
        items = OrderItem.objects.filter(order=order)
        print(f"Order #{order.id}:")
        print(f"  - Date: {order.date_odered}")
        print(f"  - Status: {order.status}")
        print(f"  - Transaction ID: {order.transaction_id}")
        print(f"  - Items: {items.count()}")
        for item in items:
            if item.product:
                print(f"    * {item.product.name} x {item.quantity}")
        print()
    
    print("\nTo fix these, we need to know which user placed these orders.")
    print("Since we can't determine this automatically, here's what you should do:")
    print("\n1. Check your payment records/emails to identify which orders are yours")
    print("2. Then run the Django shell and link them manually:")
    print("\n   python manage.py shell")
    print("   >>> from store.models import Customer, Order")
    print("   >>> from django.contrib.auth import get_user_model")
    print("   >>> User = get_user_model()")
    print("   >>> user = User.objects.get(username='your_username')")
    print("   >>> customer, _ = Customer.objects.get_or_create(user=user, defaults={'name': user.username, 'email': user.email})")
    print("   >>> Order.objects.filter(id__in=[1,2,3]).update(custamer=customer)")
    print("\n   Replace [1,2,3] with the actual order IDs")

# Check if all users have customers
print("\n" + "=" * 60)
print("CHECKING USER-CUSTOMER LINKS")
print("=" * 60)

users_without_customers = []
for user in User.objects.all():
    if not Customer.objects.filter(user=user).exists():
        users_without_customers.append(user)

if users_without_customers:
    print(f"\nFound {len(users_without_customers)} users without customer records:")
    for user in users_without_customers:
        print(f"  - {user.username} (ID: {user.id}, email: {user.email})")
        # Auto-create customer for these users
        Customer.objects.get_or_create(
            user=user,
            defaults={
                'name': user.get_full_name() or user.username,
                'email': user.email or 'no-email@example.com'
            }
        )
        print(f"    ✓ Created customer record")
else:
    print("\n✓ All users have customer records")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total users: {User.objects.count()}")
print(f"Total customers: {Customer.objects.count()}")
print(f"Total orders: {Order.objects.count()}")
print(f"Orders with customers: {Order.objects.filter(custamer__isnull=False).count()}")
print(f"Orphan orders (no customer): {Order.objects.filter(custamer__isnull=True).count()}")
print("=" * 60)
