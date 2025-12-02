#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librashop.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Customer, Order, OrderItem

User = get_user_model()

print("=" * 60)
print("DEBUGGING ORDER ISSUE")
print("=" * 60)

# Check all users
print("\n1. ALL USERS:")
for user in User.objects.all()[:10]:
    customer_count = Customer.objects.filter(user=user).count()
    print(f"   - {user.username} (ID: {user.id}): {customer_count} customer(s)")

# Check all customers
print("\n2. ALL CUSTOMERS:")
for customer in Customer.objects.all():
    order_count = Order.objects.filter(custamer=customer).count()
    user_info = customer.user.username if customer.user else "NO USER LINKED"
    print(f"   - {customer.name} (linked to: {user_info}): {order_count} order(s)")

# Check all orders
print("\n3. ALL ORDERS:")
total_orders = Order.objects.all().count()
print(f"   Total orders in database: {total_orders}")
for order in Order.objects.all()[:10]:
    customer_user = order.custamer.user.username if order.custamer and order.custamer.user else "NO USER"
    items_count = OrderItem.objects.filter(order=order).count()
    print(f"   - Order #{order.id}: customer={order.custamer.name if order.custamer else 'None'}, user={customer_user}, status={order.status}, items={items_count}")

# Check specific user 'ranjith'
print("\n4. CHECKING USER 'ranjith':")
ranjith = User.objects.filter(username='ranjith').first()
if ranjith:
    print(f"   - User exists: ID={ranjith.id}, email={ranjith.email}")
    customer = Customer.objects.filter(user=ranjith).first()
    if customer:
        print(f"   - Has customer: {customer.name}")
        orders = Order.objects.filter(custamer=customer)
        print(f"   - Orders: {orders.count()}")
        for order in orders:
            print(f"     * Order #{order.id}, status={order.status}")
    else:
        print(f"   - NO CUSTOMER RECORD FOR THIS USER!")
        print(f"   - Checking orders with customer name matching user...")
        customers_with_similar_name = Customer.objects.filter(name__icontains='ranjith')
        for c in customers_with_similar_name:
            print(f"     * Found customer: {c.name}, user={c.user.username if c.user else 'NO USER'}")
else:
    print("   - User 'ranjith' not found!")

print("\n" + "=" * 60)
