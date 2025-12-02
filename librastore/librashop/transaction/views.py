from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from cart.views import get_user_cart
from django.contrib import messages
import stripe
from django.urls import reverse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
import json
from cart.models import Cart, CartItem
from transaction.models import Order, Transaction, OrderItem
from store.models import Product
from django.core.mail import send_mail
from django.template.loader import render_to_string


# Create your views here.

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def strip_webhook(request):
      payload = request.body
      sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
      event = None

      try:
          event = stripe.Webhook.construct_event(
               payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
          )

      except ValueError as e:
          return HttpResponse(status=400)
      except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)
      if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_completed_checkout_session(session)
      return HttpResponse(status=200)

def handle_completed_checkout_session(session):
      with transaction.atomic():
            user_id = session.metadata.get('user_id')
            cart_id = session.metadata.get('cart_id')
            shipping_address = session.metadata.get('shipping_address')


            if not user_id or not cart_id:
                  return
            
            try:
                cart = Cart.objects.get(id=cart_id)
                user = User.objects.get(id=user_id)

            except (Cart.DoesNotExist, User.DoesNotExist):
                   return
            
            order = Order.objects.create(
                  user=user,
                  cart=cart,
                  stripe_id=session.id,
                  amount_total=session.amount_total /100,
                  shipping_address=shipping_address,
                  status='paid',
            )


            for cart_item in cart.items.all():
                  OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.price_at_addition,

                  )

            cart.items.all().delete()



            Transaction.objects.create(
                  order=order,
                  transaction_id=session.payment_intent,
                  amount=order.amount_total,
                  status='succeeded',
                  payment_method=session.payment_method_types
            )


            email_subject = 'Your Order Confirmation from LIBRA'
            email_body = render_to_string('emails/order_confirmation.html', {'order':order})
            send_mail(
                  email_subject,
                  email_body,
                  settings.DEFAULT_FROM_EMAIL,
                  [user.email],
                  fail_silently=False,  
            )

@login_required
def create_checkout_session(request):
    cart = get_user_cart(request)
    if not cart.items.exists():
            messages.error(request, 'Your Cart Is Empty!')
            return redirect('cart_summary')
    

    shipping_address_id = request.session.get("shipping_address_id")
    if not shipping_address_id:
         messages.error(request, "Please Enter A Shipping Address!")
         return redirect('checkout')
    

    # Build line items and apply coupon discount if any
    line_items = []
    items = list(cart.items.all())
    # Compute subtotal in paise
    subtotal_paise = 0
    for it in items:
        if it.product and it.price_at_addition:
            subtotal_paise += int(it.price_at_addition * 100) * int(it.quantity)
    
    # Read coupon from session
    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount_paise_total = 0
    if coupon_code and subtotal_paise > 0:
        try:
            from coupons.models import Coupon
            from django.utils import timezone
            now = timezone.now()
            coupon = Coupon.objects.filter(code__iexact=coupon_code, active=True, valid_from__lte=now, valid_to__gte=now).first()
            if coupon:
                if coupon.discount_type == 'Percentage':
                    discount_paise_total = int(subtotal_paise * (float(coupon.value) / 100.0))
                else:
                    discount_paise_total = int(float(coupon.value) * 100)
                    if discount_paise_total > subtotal_paise:
                        discount_paise_total = subtotal_paise
        except Exception:
            coupon = None
            discount_paise_total = 0

    # Build discounted line items
    for it in items:
        if not (it.product and it.price_at_addition):
            continue
        unit_amount = int(it.price_at_addition * 100)
        qty = int(it.quantity)

        # Adjust by percentage easily
        if coupon and discount_paise_total and subtotal_paise > 0:
            if coupon.discount_type == 'Percentage':
                unit_amount = int(unit_amount * (1 - float(coupon.value) / 100.0))
            else:
                # Fixed: prorate discount across items
                item_total = unit_amount * qty
                item_share = item_total / subtotal_paise
                item_discount_total = int(discount_paise_total * item_share)
                per_unit_discount = int(item_discount_total / max(qty, 1))
                unit_amount = max(0, unit_amount - per_unit_discount)

        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': it.product.name,
                },
                'unit_amount': unit_amount,
            },
            'quantity': qty,
        })
                
    if not line_items:
         messages.error(request, "Your Cart Is Empty Or Contains Invalid Items!")
         return redirect('cart_summary')
    
    # Get shipping address for Indian export compliance
    from store.models import ShippingAdderss
    shipping_address = None
    try:
        shipping_address = ShippingAdderss.objects.get(id=shipping_address_id)
    except ShippingAdderss.DoesNotExist:
        pass
    
    try:
        # Prepare customer details for Indian regulations
        customer_details = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
        }
        
        # Add address if available (required for Indian exports)
        if shipping_address:
            customer_details['address'] = {
                'line1': shipping_address.address,
                'city': shipping_address.city,
                'state': shipping_address.state,
                'postal_code': shipping_address.zipcode,
                'country': 'IN',  # India
            }
        
        # Build session parameters
        session_params = {
            'line_items': line_items,
            'mode': 'payment',
            'customer_email': request.user.email,
            'billing_address_collection': 'required',  # Required for Indian exports
            'success_url': (
                request.build_absolute_uri(reverse("order_success"))
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            'cancel_url': request.build_absolute_uri(reverse("checkout")),
            'metadata': {
                'user_id': request.user.id,
                'cart_id': cart.id,
                'shipping_addredd_id': shipping_address_id,
                'customer_name': customer_details['name'],
                'customer_email': customer_details['email'],
            }
        }
            
        # Add shipping address collection if no address provided
        if not shipping_address:
            session_params['shipping_address_collection'] = {
                'allowed_countries': ['IN'],  # India
            }
        
        checkout_session = stripe.checkout.Session.create(**session_params)
        session_url = getattr(checkout_session, "url", None)
        if not session_url:
            messages.error(request, "Unable to start checkout: no session URL returned.")
            return redirect('checkout')
        return redirect(session_url, code=303)
        
    except Exception as e:
            messages.error(request, f"An error occurred during checkout : {e}")
            return redirect('checkout')
    


def payment_success(request):
      return render(request, 'success.html')


def payment_cancel(request):
      return render(request, 'cancel.html')
