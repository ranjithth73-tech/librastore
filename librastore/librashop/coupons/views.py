from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal

from .models import Coupon
from cart.views import get_user_cart


def apply_coupon(request):
    if request.method != 'POST':
        return redirect('checkout')

    code = (request.POST.get('coupon', '') or '').strip()
    if not code:
        messages.error(request, 'Please enter a coupon code.')
        return redirect('checkout')

    now = timezone.now()
    coupon = Coupon.objects.filter(code__iexact=code, active=True, valid_from__lte=now, valid_to__gte=now).first()
    if not coupon:
        messages.error(request, 'Invalid or expired coupon.')
        return redirect('checkout')

    # Optionally validate against cart total
    try:
        cart = get_user_cart(request)
        if not cart.items.exists():
            messages.error(request, 'Your Cart Is Empty!')
            return redirect('checkout')
    except Exception:
        pass

    # Store applied coupon in session
    request.session['coupon_code'] = coupon.code
    messages.success(request, f"Coupon '{coupon.code}' applied.")
    return redirect('checkout')


def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon removed.')
    return redirect('checkout')


def offers(request):
    """Display all active coupons and offers"""
    now = timezone.now()
    
    # Get all active coupons that are currently valid
    active_coupons = Coupon.objects.filter(
        active=True,
        valid_from__lte=now,
        valid_to__gte=now
    ).order_by('-value')
    
    # Separate by discount type
    percentage_coupons = active_coupons.filter(discount_type='Percentage')
    fixed_coupons = active_coupons.filter(discount_type='Fixed')
    
    context = {
        'active_coupons': active_coupons,
        'percentage_coupons': percentage_coupons,
        'fixed_coupons': fixed_coupons,
        'total_offers': active_coupons.count(),
    }
    return render(request, 'offers.html', context)
