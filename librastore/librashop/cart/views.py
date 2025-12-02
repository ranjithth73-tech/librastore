from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from store.models import Product, Customer
from .models import Cart, CartItem
# Create your views here.


def get_user_cart(request):

    # Get or create customer for the user
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or 'no-email@example.com'
        }
    )
    cart, created = Cart.objects.get_or_create(customer=customer)
    return cart



@login_required
def view_cart(request):
    cart_instance = get_user_cart(request)
    context = {'cart':cart_instance}
    return render(request, 'cart.html', context)




@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Use quantity from POST; fallback to 1 for non-POST (e.g., link click)
    try:
        quantity = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
    except (TypeError, ValueError):
        quantity = 1

    cart = get_user_cart(request)   

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            'quantity': quantity,
            'price_at_addition': product.price
        }
    )
    if not item_created:
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f"Added {quantity} more of {product.name} to your cart.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    # Support Buy Now flow: redirect to 'next' if provided and safe
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    try:
        checkout_url = reverse('checkout')
    except Exception:
        checkout_url = '/checkout/'
    if next_url in (checkout_url, '/checkout/'):
        return redirect(checkout_url)
    return redirect('view_cart')
    
    

@require_POST
@login_required
def update_cart(request, item_id):
    cart = get_user_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()

    else:
        cart_item.delete()

    return redirect('view_cart')

@login_required
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    # Find item only within this user's cart; handle missing gracefully
    cart_item = CartItem.objects.filter(id=item_id, cart=cart).first()
    if not cart_item:
        messages.error(request, "Item not found in your cart or already removed.")
        return redirect('view_cart')
    cart_item.delete()
    messages.success(request, "Item has been removed from your cart.")
    return redirect('view_cart')

def get_or_create_cart(request):
    if request.user.is_authenticated:
        # Get or create customer for the user
        customer, created = Customer.objects.get_or_create(
            user=request.user,
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email or 'no-email@example.com'
            }
        )
        cart, created = Cart.objects.get_or_create(customer = customer)
        
        return cart
    

    else:
        session_key = request.session.session_key

        if not session_key:
            request.session.save()
            session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(session_key = session_key, defaults={'customer':None})

        
        return cart