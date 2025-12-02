def cart_wishlist_counts(request):
    from store.models import Customer
    from cart.models import Cart, Wishlist, WishlistItem
    
    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:
        try:
            # Get customer
            customer = Customer.objects.filter(user=request.user).first()
            if customer:
                # Count cart items
                cart = Cart.objects.filter(customer=customer).first()
                if cart:
                    cart_count = cart.items.count()
                
                # Count wishlist items (cart app models)
                wishlist = Wishlist.objects.filter(customer=customer).first()
                if wishlist:
                    wishlist_count = WishlistItem.objects.filter(wishlist=wishlist).count()
        except Exception:
            pass

    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count
    }