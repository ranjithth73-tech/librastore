from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from . forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
from store.models import Order, OrderItem, Wishlist, Product, ContactMessage, Customer
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse



# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '')
            return redirect('home')
        else:
            messages.error(request, '')

    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data = request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome {username}.")
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request,'Enter the correct details')
        else:
            messages.error(request, 'Enter the correct details')

    else:
        form = AuthenticationForm()

    context = {'form':form}
    return render(request, 'login.html', context)


@require_POST
def logout(request):
    
    auth_logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('home')
    
@login_required
def order_history(request):
    # Get customer object for the logged-in user
    customer = Customer.objects.filter(user=request.user).first()
    
    if customer:
        # Filter orders by customer (note: field is misspelled as 'custamer' in model)
        orders = Order.objects.filter(custamer=customer).order_by('-date_odered')
    else:
        orders = Order.objects.none()
    
    context = {'orders': orders}
    return render(request, 'order_history.html', context)


@login_required
def user_profile(request):
    """View for user profile page"""
    from store.models import Customer
    
    # Get or create customer for the user
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or 'no-email@example.com'
        }
    )
    
    context = {
        'user': request.user,
        'customer': customer,
    }
    return render(request, 'user_profile.html', context)


@login_required
def my_orders(request):
    """View for user's order history"""
    from store.models import Customer
    
    # Get or create customer for the user
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or 'no-email@example.com'
        }
    )
    
    # Debug: Print customer info
    print(f"DEBUG - User: {request.user.username}, Customer ID: {customer.id}, Customer Name: {customer.name}")
    
    # Get all orders for this customer
    orders = Order.objects.filter(custamer=customer).order_by('-date_odered')
    
    # Debug: Print order count
    print(f"DEBUG - Orders found: {orders.count()}")
    
    # Tracking stage progress mapping
    tracking_progress = {
        'placed': {'percent': 5, 'label': 'Placed'},
        'confirmed': {'percent': 20, 'label': 'Confirmed'},
        'packed': {'percent': 40, 'label': 'Packed'},
        'shipped': {'percent': 65, 'label': 'Shipped'},
        'out_for_delivery': {'percent': 85, 'label': 'Out for delivery'},
        'delivered': {'percent': 100, 'label': 'Delivered'},
        'cancelled': {'percent': 0, 'label': 'Cancelled'},
    }

    # Get order items for each order
    orders_with_items = []
    for order in orders:
        items = OrderItem.objects.filter(order=order).select_related('product')
        order_total = sum(getattr(item, 'line_total', 0) for item in items)
        stage = getattr(order, 'tracking_stage', 'placed') or 'placed'
        progress = tracking_progress.get(stage, tracking_progress['placed'])
        print(f"DEBUG - Order {order.id}: {items.count()} items, Total: {order_total}")
        orders_with_items.append({
            'order': order,
            'items': items,
            'total': order_total,
            'tracking': {
                'percent': progress['percent'],
                'label': progress['label'],
                'tracking_number': getattr(order, 'tracking_number', ''),
                'carrier': getattr(order, 'carrier', ''),
            }
        })
    
    context = {
        'orders_with_items': orders_with_items,
        'total_orders': orders.count(),
    }
    return render(request, 'my_orders.html', context)


@login_required
def my_orders_status(request):
    """Lightweight JSON for polling order tracking/status without reloading the page"""
    from store.models import Customer
    customer, _ = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or 'no-email@example.com'
        }
    )
    tracking_progress = {
        'placed': {'percent': 5, 'label': 'Placed'},
        'confirmed': {'percent': 20, 'label': 'Confirmed'},
        'packed': {'percent': 40, 'label': 'Packed'},
        'shipped': {'percent': 65, 'label': 'Shipped'},
        'out_for_delivery': {'percent': 85, 'label': 'Out for delivery'},
        'delivered': {'percent': 100, 'label': 'Delivered'},
        'cancelled': {'percent': 0, 'label': 'Cancelled'},
    }
    orders = Order.objects.filter(custamer=customer).order_by('-date_odered')
    payload = []
    for o in orders:
        stage = getattr(o, 'tracking_stage', 'placed') or 'placed'
        progress = tracking_progress.get(stage, tracking_progress['placed'])
        payload.append({
            'id': o.id,
            'status': o.status,
            'tracking_stage': stage,
            'tracking_label': progress['label'],
            'percent': progress['percent'],
            'tracking_number': getattr(o, 'tracking_number', '') or '',
            'carrier': getattr(o, 'carrier', '') or '',
        })
    return JsonResponse({'orders': payload})


@login_required
def wishlist(request):
    """View for user's wishlist"""
    from store.models import Customer
    from cart.models import Wishlist, WishlistItem
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    wishlist_obj, _ = Wishlist.objects.get_or_create(customer=customer, defaults={'name': 'My Wishlist'})
    items = WishlistItem.objects.filter(wishlist=wishlist_obj).select_related('product')
    
    context = {
        'items': items, 
        'wishlist_items': items,  # For backwards compatibility
        'total_items': items.count(),
    }
    return render(request, 'wishlist.html', context)


@login_required
def add_to_wishlist(request, product_id):
    """Add a product to wishlist"""
    from store.models import Customer
    from cart.models import Wishlist, WishlistItem
    
    product = get_object_or_404(Product, id=product_id)
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    wishlist_obj, _ = Wishlist.objects.get_or_create(customer=customer, defaults={'name': 'My Wishlist'})
    
    # Check if already in wishlist
    if not WishlistItem.objects.filter(wishlist=wishlist_obj, product=product).exists():
        WishlistItem.objects.create(wishlist=wishlist_obj, product=product)
        messages.success(request, f'{product.name} added to your wishlist!')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))
    

@login_required
def remove_from_wishlist(request, wishlist_id):
    """Remove a product from wishlist"""
    from store.models import Customer
    from cart.models import Wishlist, WishlistItem
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    wishlist_obj = get_object_or_404(Wishlist, customer=customer)
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_id, wishlist=wishlist_obj)
    product_name = wishlist_item.product.name
    wishlist_item.delete()
    
    messages.success(request, f'{product_name} removed from your wishlist.')
    return redirect('wishlist')


def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'contact.html')


@login_required
def debug_orders(request):
    """Debug view to show order information"""
    from store.models import Customer
    
    # Get current user info
    user_info = {
        'username': request.user.username,
        'email': request.user.email,
        'id': request.user.id,
    }
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or 'no-email@example.com'
        }
    )
    
    # Get orders for this customer
    orders = Order.objects.filter(custamer=customer)
    
    # Get ALL orders (for debugging)
    all_orders = Order.objects.all()
    orphan_orders = Order.objects.filter(custamer__isnull=True)
    
    context = {
        'user_info': user_info,
        'customer': customer,
        'customer_created': created,
        'orders': orders,
        'all_orders_count': all_orders.count(),
        'orphan_orders_count': orphan_orders.count(),
    }
    
    return render(request, 'debug_orders.html', context)


