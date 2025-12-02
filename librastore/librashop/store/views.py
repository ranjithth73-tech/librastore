from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count, F, OuterRef, Subquery
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.templatetags.static import static
import stripe
import logging

from .models import Product, Customer, Order, OrderItem, ShippingAdderss, Category
from .forms import ShippingAdderssForm
from cart.models import Cart, CartItem, Wishlist, WishlistItem
 
# Create your views here.

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY



def home(request):
    """
    Home page view - displays all categories with their products in grid layout.
    Each category shows up to 8 products.
    """
    # Get all categories
    categories = Category.objects.all()
    all_categories = categories  # expose full list for category cards section
    
    # Build a list of categories with their products
    categories_with_products = []
    for category in categories:
        # Include products linked via FK and avoid duplicates
        products = Product.objects.filter(
            Q(category=category),
            available=True
        )
        # Deduplicate by slug: keep newest per slug
        latest_per_slug = Product.objects.filter(slug=OuterRef('slug')).order_by('-created', '-id').values('id')[:1]
        products = products.annotate(latest_id=Subquery(latest_per_slug)).filter(id=F('latest_id'))[:8]
        if products.exists():  # Only show categories that have products
            categories_with_products.append({
                'category': category,
                'products': products
            })

    # Featured banners: pick latest available products (up to 3)
    try:
        featured_products = list(Product.objects.filter(available=True).order_by('-created')[:3])
    except Exception:
        featured_products = []
    
    # Build hero images list (configurable via settings.HOME_HERO_IMAGES)
    try:
        custom_imgs = getattr(settings, 'HOME_HERO_IMAGES', None)
        if custom_imgs:
            hero_images = [static(p) if isinstance(p, str) and not str(p).startswith('http') else p for p in custom_imgs]
        else:
            hero_images = [
                static('images/banners/banner1.jpg'),
                static('images/banners/banner2.jpg'),
                static('images/banners/banner3.jpg'),
            ]
    except Exception:
        hero_images = [
            static('images/banners/banner1.jpg'),
            static('images/banners/banner2.jpg'),
            static('images/banners/banner3.jpg'),
        ]

    context = {
        'categories_with_products': categories_with_products,
        'all_categories': all_categories,
        'featured_products': featured_products,
        'hero_images': hero_images,
    }
    return render(request, 'home.html', context)


def shop(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '').strip()
    products = Product.objects.all()
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        ).distinct()
    # Deduplicate by slug before sorting (to avoid duplicates from cloned rows)
    latest_per_slug = Product.objects.filter(slug=OuterRef('slug')).order_by('-created', '-id').values('id')[:1]
    products = products.annotate(latest_id=Subquery(latest_per_slug)).filter(id=F('latest_id'))

    # Sorting
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    else:
        # Default sorting: newest first
        products = products.order_by('-created')
    
    context = {'products': products, 'q': q, 'sort': sort}
    return render(request, 'shop.html', context)

def category_shop(request, slug):
    category = get_object_or_404(Category, slug=slug)
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '').strip()
    products = Product.objects.filter(Q(category=category)).distinct()
    # Deduplicate by slug within this category view
    latest_per_slug = Product.objects.filter(slug=OuterRef('slug')).order_by('-created', '-id').values('id')[:1]
    products = products.annotate(latest_id=Subquery(latest_per_slug)).filter(id=F('latest_id'))
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q)
        ).distinct()
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    else:
        products = products.order_by('-created')

    # Determine hero video URL for this category using only admin-uploaded file
    hero_video_url = category.hero_video.url if getattr(category, 'hero_video', None) else None

    context = {
        'category': category,
        'products': products,
        'q': q,
        'sort': sort,
        'hero_video_url': hero_video_url,
    }
    return render(request, 'category_shop.html', context)

def product_details(request, slug):
    # Handle case where slug is not unique by selecting the most recent product
    products_qs = Product.objects.filter(slug=slug).order_by('-created', '-id')
    product = products_qs.first()
    if product is None:
        from django.http import Http404
        raise Http404("Product not found")
    # Gallery images
    gallery = getattr(product, 'images', None)
    images = gallery.all() if gallery is not None else []
    # Simple similar products (same category via FK or M2M)
    similar_q = Q()
    if getattr(product, 'category', None):
        similar_q |= Q(category=product.category)
    # No M2M categories on Product; only use FK category
    similar_products = Product.objects.filter(similar_q).exclude(id=product.id).distinct()[:8]
    context = {
        'product': product,
        'images': images,
        'similar_products': similar_products,
    }
    return render(request, 'products_details.html', context)

def product_details_by_id(request, pk):
    # Load a specific product by primary key to avoid slug collisions
    product = get_object_or_404(Product, pk=pk)
    # Gallery images
    gallery = getattr(product, 'images', None)
    images = gallery.all() if gallery is not None else []
    # Simple similar products (same category via FK)
    similar_q = Q()
    if getattr(product, 'category', None):
        similar_q |= Q(category=product.category)
    similar_products = Product.objects.filter(similar_q).exclude(id=product.id).distinct()[:8]
    context = {
        'product': product,
        'images': images,
        'similar_products': similar_products,
    }
    return render(request, 'products_details.html', context)

@login_required
def checkout(request):
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    
    try:
        cart_instance = Cart.objects.get(customer=customer)
        subtotal = cart_instance.get_total()
    except Cart.DoesNotExist:
        messages.error(request, "Your Cart Is Empty.")
        return redirect('cart_summary')

    if not cart_instance.items.exists():
        messages.error(request, "Your Cart Is Empty")
        return redirect('cart_summary')
    
    # Coupon calculations (display only; Stripe amounts adjusted in transaction/views.py)
    discount = 0
    applied_coupon = None
    try:
        from coupons.models import Coupon
        code = request.session.get('coupon_code')       
        if code:
            from django.utils import timezone
            now = timezone.now()
            applied_coupon = Coupon.objects.filter(code__iexact=code, active=True, valid_from__lte=now, valid_to__gte=now).first()
            if applied_coupon:
                if applied_coupon.discount_type == 'Percentage':
                    discount = round(float(subtotal) * float(applied_coupon.value) / 100.0, 2)
                else:
                    discount = min(float(applied_coupon.value), float(subtotal))
    except Exception:
        pass
    grand_total = float(subtotal) - float(discount)

    if request.method == 'POST':
        form = ShippingAdderssForm(request.POST)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.customer = customer #request.user if request.user.is_authenticated else None
            shipping_address.order = None
            shipping_address.save()

            request.session['shipping_address_id'] = shipping_address.id

            return redirect('create_checkout_session')
        

    else:
            
            form = ShippingAdderssForm()

    context = {
         'cart': cart_instance,
         'subtotal': subtotal,
         'discount': discount,
         'grand_total': grand_total,
         'applied_coupon': applied_coupon,
         'form': form
    }
    return render(request,'checkout.html', context)


    

@login_required  
def order_success(request):
        session_id = request.GET.get('session_id')
        if session_id:
             try:
                  session = stripe.checkout.Session.retrieve(session_id)
                  if session.payment_status == 'paid':
                       # Locate the cart: if user is authenticated, use customer cart; otherwise use session cart
                       cart_instance = None
                       if request.user.is_authenticated:
                            customer, _ = Customer.objects.get_or_create(
                                 user=request.user,
                                 defaults={
                                      'name': request.user.get_full_name() or request.user.username,
                                      'email': request.user.email or 'no-email@example.com'
                                 }
                            )
                            cart_instance = Cart.objects.filter(customer=customer).first()
                       if cart_instance is None:
                            cart_instance = Cart.objects.filter(session_key=request.session.session_key).first()
                       if not cart_instance:
                            return render(request, 'order_success.html')
                       
                       

                       # Get or create customer
                       customer, created = Customer.objects.get_or_create(
                            user=request.user if request.user.is_authenticated else None,
                            defaults={
                                'name': request.user.get_full_name() or request.user.username,
                                'email': request.user.email or 'no-email@example.com'
                            }
                       )
                        
                       order = Order.objects.create(
                             custamer = customer,
                             complete = True,
                             status='paid',
                             transaction_id = session.payment_intent
                       )
                       for cart_item in cart_instance.items.all():
                            prod = cart_item.product
                            OrderItem.objects.create(
                                 order=order,
                                 product=prod,
                                 quantity=cart_item.quantity,
                                 product_name=(prod.name if prod else None),
                                 product_price=(prod.price if prod else None),
                                 product_image=(prod.image.url if (prod and getattr(prod, 'image', None)) else None),
                            )
                       shipping_address_id = request.session.get('shipping_address_id')
                       if shipping_address_id:
                            shipping_address = ShippingAdderss.objects.get(id = shipping_address_id)
                            shipping_address.order = order
                            shipping_address.save()
                            del request.session['shipping_address_id']

                       cart_instance.items.all().delete()
                       cart_instance.delete()
                       
                       return render(request, 'order_success.html')
                  else:
                       return render(request, 'order_cancel.html')
                  
             except (Cart.DoesNotExist, ShippingAdderss.DoesNotExist, Exception) as e:
                  logger.error(f"Error in order_success: {e}")
                  return render(request, 'order_cancel.html')
        return redirect('home')    

@login_required
def order_cancel(request):
     return render(request, 'order_cancel.html')


@login_required
def wishlist(request):
     # Get or create customer
     customer, created = Customer.objects.get_or_create(
         user=request.user,
         defaults={'name': request.user.username, 'email': request.user.email}
     )
     wishlist, _ = Wishlist.objects.get_or_create(customer=customer, defaults={'name': 'My Wishlist'})
     items = WishlistItem.objects.filter(wishlist=wishlist).select_related('product')
     context = { 'items': items }
     return render(request, 'wishlist.html', context)


@login_required
def add_to_wishlist(request, product_id):
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    wishlist, _ = Wishlist.objects.get_or_create(customer=customer, defaults={'name': 'My Wishlist'})
    product = get_object_or_404(Product, id=product_id)
    
    # Check if already in wishlist
    if not WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        messages.success(request, f'{product.name} added to wishlist!')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def remove_from_wishlist(request, item_id):
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    wishlist = get_object_or_404(Wishlist, customer=customer)
    item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    product_name = item.product.name
    item.delete()
    messages.success(request, f'{product_name} removed from wishlist.')
    return redirect('wishlist')



def about_view(request):
     return render(request, 'about.html')


@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with sales analytics"""
    
    # Total counts
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    
    # Calculate total revenue from completed orders
    total_revenue = 0
    completed_orders = Order.objects.filter(complete=True)
    for order in completed_orders:
        try:
            total_revenue += order.get_cart_total
        except:
            pass
    
    # Top selling products (most ordered)
    top_products = OrderItem.objects.values('product__name', 'product__id').annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('quantity')
    ).order_by('-total_sold')[:10]
    
    # Low selling products (least ordered or never ordered)
    all_products = Product.objects.all()
    product_sales = {}
    for product in all_products:
        sold = OrderItem.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        product_sales[product.id] = {
            'name': product.name,
            'sold': sold,  
            'sold': sold,   
            'price': product.price,    
            'price': product.price,     
            'stock': getattr(product, 'stock', 0)
        }
    
    # Sort by lowest sales
    low_selling = sorted(product_sales.items(), key=lambda x: x[1]['sold'])[:10]
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-date_odered')[:10]
    
    # Category-wise sales
    category_sales = OrderItem.objects.values('product__category__name').annotate(
        total=Sum('quantity')
    ).order_by('-total')[:5]
    
    # Monthly revenue (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_orders = Order.objects.filter(
        date_odered__gte=six_months_ago,
        complete=True
    ).extra(select={'month': 'strftime("%%Y-%%m", date_odered)'}).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'top_products': top_products,
        'low_selling': low_selling,
        'recent_orders': recent_orders,
        'category_sales': category_sales,
        'monthly_orders': monthly_orders,
    }
    
    return render(request, 'admin_dashboard.html', context)


