"""
Custom Admin Views - Replicate Django admin functionality with custom interface
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

from .models import Product, Category, Order, OrderItem, Customer, ShippingAdderss
from .forms import ShippingAdderssForm
from coupons.models import Coupon, OrderCoupon


# ============= REDIRECT TO DJANGO ADMIN =============

@staff_member_required
def admin_redirect(request, subpath: str = ""):
    """Redirect any custom-admin URL to the built-in Django admin.

    This keeps old bookmarks/links working while consolidating management
    into the standard Django admin at /admin/.
    """
    return redirect('/admin/')

# ============= PRODUCT MANAGEMENT =============

@staff_member_required
def admin_products_list(request):
    """List all products with search and pagination"""
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    
    products = Product.objects.all().order_by('-created')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )   
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    
    categories = Category.objects.all()
    
    context = {
        'products': products_page,
        'categories': categories,
        'query': query,
        'category_filter': category_filter,
        'total_count': products.count(),
    }
    return render(request, 'custom_admin/products_list.html', context)


@csrf_protect
@staff_member_required
def admin_product_add(request):
    """Add new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id) if category_id else None
            product = Product.objects.create(
                name=name,
                price=price,
                description=description,
                category=category,
                image=image
            )
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('admin_products_list')
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'custom_admin/product_form.html', context)


@csrf_protect
@staff_member_required
def admin_product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        category_id = request.POST.get('category')
        
        if category_id:
            product.category = Category.objects.get(id=category_id)
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('admin_products_list')
    
    categories = Category.objects.all()
    context = {
        'product': product,
        'categories': categories,
        'is_edit': True
    }
    return render(request, 'custom_admin/product_form.html', context)


@staff_member_required
def admin_product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f'Product "{product_name}" deleted successfully!')
    return redirect('admin_products_list')


# ============= ORDER MANAGEMENT =============

@staff_member_required
def admin_orders_list(request):
    """List all orders with filters"""
    # Redirect to Django admin's Order changelist
    try:
        return redirect(reverse('admin:store_order_changelist'))
    except Exception:
        # Fallback hardcoded path if reverse fails
        return redirect('/admin/store/order/')


@staff_member_required
def admin_order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    try:
        shipping = ShippingAdderss.objects.get(order=order)
    except ShippingAdderss.DoesNotExist:
        shipping = None
    
    context = {
        'order': order,
        'order_items': order_items,
        'shipping': shipping,
    }
    return render(request, 'custom_admin/order_detail.html', context)


@staff_member_required
def admin_order_update_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        complete = request.POST.get('complete') == 'on'
        
        order.status = status
        order.complete = complete
        order.save()
        
        messages.success(request, f'Order #{order.id} status updated!')
        return redirect('admin_order_detail', order_id=order.id)
    
    return redirect('admin_orders_list')


# ============= CUSTOMER MANAGEMENT =============

@staff_member_required
def admin_customers_list(request):
    """List all customers"""
    query = request.GET.get('q', '')
    
    customers = Customer.objects.all().order_by('-id')
    
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(customers, 20)
    page = request.GET.get('page', 1)
    customers_page = paginator.get_page(page)
    
    context = {
        'customers': customers_page,
        'query': query,
        'total_count': customers.count(),
    }
    return render(request, 'custom_admin/customers_list.html', context)


@staff_member_required
def admin_customer_detail(request, customer_id):
    """View customer details and orders"""
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(custamer=customer).order_by('-date_odered')
    
    context = {
        'customer': customer,
        'orders': orders,
        'total_orders': orders.count(),
        'completed_orders': orders.filter(complete=True).count(),
    }
    return render(request, 'custom_admin/customer_detail.html', context)


# ============= COUPON MANAGEMENT =============

@staff_member_required
def admin_coupons_list(request):
    """List all coupons"""
    from django.utils import timezone
    
    coupons = Coupon.objects.all().order_by('-valid_from')
    now = timezone.now()
    
    # Pagination
    paginator = Paginator(coupons, 20)
    page = request.GET.get('page', 1)
    coupons_page = paginator.get_page(page)
    
    context = {
        'coupons': coupons_page,
        'total_count': coupons.count(),
        'now': now,
    }
    return render(request, 'custom_admin/coupons_list.html', context)


@staff_member_required
def admin_coupon_add(request):
    """Add new coupon"""
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_type = request.POST.get('discount_type')
        value = request.POST.get('value')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        active = request.POST.get('active') == 'on'
        max_users = request.POST.get('max_users', 0)
        
        try:
            coupon = Coupon.objects.create(
                code=code.upper(),
                discount_type=discount_type,
                value=value,
                valid_from=valid_from,
                valid_to=valid_to,
                active=active,
                max_users=max_users
            )
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('admin_coupons_list')
        except Exception as e:
            messages.error(request, f'Error creating coupon: {str(e)}')
    
    context = {}
    return render(request, 'custom_admin/coupon_form.html', context)


@staff_member_required
def admin_coupon_edit(request, coupon_id):
    """Edit existing coupon"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':    
        coupon.code = request.POST.get('code').upper()
        coupon.discount_type = request.POST.get('discount_type')
        coupon.value = request.POST.get('value')
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_to = request.POST.get('valid_to')
        coupon.active = request.POST.get('active') == 'on'
        coupon.max_users = request.POST.get('max_users', 0)
        coupon.save()
        
        messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
        return redirect('admin_coupons_list')
    
    context = {
        'coupon': coupon,
        'is_edit': True
    }
    return render(request, 'custom_admin/coupon_form.html', context)


@staff_member_required
def admin_coupon_delete(request, coupon_id):
    """Delete coupon"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon_code = coupon.code
    coupon.delete()
    messages.success(request, f'Coupon "{coupon_code}" deleted successfully!')
    return redirect('admin_coupons_list')


@staff_member_required
def admin_coupon_toggle(request, coupon_id):
    """Toggle coupon active status"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.active = not coupon.active
    coupon.save()
    
    status = "activated" if coupon.active else "deactivated"
    messages.success(request, f'Coupon "{coupon.code}" {status}!')
    return redirect('admin_coupons_list')


# ============= CATEGORY MANAGEMENT =============

@staff_member_required
def admin_categories_list(request):
    """List all categories"""
    categories = Category.objects.all().order_by('name')
    
    context = {
        'categories': categories,
        'total_count': categories.count(),
    }
    return render(request, 'custom_admin/categories_list.html', context)


@staff_member_required
def admin_category_add(request):
    """Add new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or ''
        hero_video = request.FILES.get('hero_video')

        try:
            final_slug = slugify(name) if not slug.strip() else slug.strip()
            category = Category.objects.create(name=name, slug=final_slug)
            if hero_video:
                category.hero_video = hero_video
                category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_categories_list')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    
    return render(request, 'custom_admin/category_form.html', {})


@staff_member_required
def admin_category_edit(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        new_slug = request.POST.get('slug') or ''
        if new_slug.strip():
            category.slug = new_slug.strip()
        else:
            # If slug left blank, regenerate from name (keeps uniqueness constraint in DB)
            category.slug = slugify(category.name)
        if request.FILES.get('hero_video'):
            category.hero_video = request.FILES.get('hero_video')
        category.save()
        
        messages.success(request, f'Category "{category.name}" updated successfully!')
        return redirect('admin_categories_list')
    
    context = {
        'category': category,
        'is_edit': True
    }
    return render(request, 'custom_admin/category_form.html', context)


@staff_member_required
def admin_category_delete(request, category_id):
    """Delete category"""
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    category.delete()
    messages.success(request, f'Category "{category_name}" deleted successfully!')
    return redirect('admin_categories_list')


# ============= DASHBOARD (GRAPHICAL) =============

@staff_member_required
def admin_dashboard(request):
    """Overview dashboard with key KPIs and charts."""
    now = timezone.now()
    start_date = now - timedelta(days=6)

    # Orders per day (last 7 days)
    orders_qs = (
        Order.objects.filter(date_odered__date__gte=start_date.date())
        .extra(select={'day': "date(date_odered)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    orders_labels = [str(item['day']) for item in orders_qs]
    orders_counts = [item['count'] for item in orders_qs]

    # Revenue per day (paid orders only)
    paid_orders = Order.objects.filter(date_odered__date__gte=start_date.date(), status='paid')
    # compute revenue in Python to respect line_total helper safely
    revenue_map = {}
    for o in paid_orders:
        d = o.date_odered.date()
        revenue_map[d] = revenue_map.get(d, 0) + float(o.get_cart_total or 0)
    revenue_labels = [str(d) for d in sorted(revenue_map.keys())]
    revenue_values = [revenue_map[d] for d in sorted(revenue_map.keys())]

    # Top categories by product count
    top_categories_qs = (
        Category.objects.annotate(pcount=Count('products')).order_by('-pcount')[:5]
    )
    top_cat_labels = [c.name for c in top_categories_qs]    
    top_cat_counts = [c.pcount or 0 for c in top_categories_qs]

    # Order status breakdown
    status_map = dict(list(Order._meta.get_field('status').choices or []))
    status_counts_qs = (
        Order.objects.values('status').annotate(cnt=Count('id')).order_by()
    )
    status_labels = [status_map.get(item['status'], item['status']) for item in status_counts_qs]
    status_counts = [item['cnt'] for item in status_counts_qs]

    # Coupon usage (requires OrderCoupon)
    coupon_usage_qs = (
        OrderCoupon.objects.values('coupon__code').annotate(cnt=Count('id')).order_by('-cnt')[:7]
    )
    coupon_labels = [item['coupon__code'] or 'N/A' for item in coupon_usage_qs]
    coupon_counts = [item['cnt'] for item in coupon_usage_qs]
        
    # Top products by quantity (OrderItem)
    top_products_qs = (
        OrderItem.objects.values('product_name').annotate(qty=Sum('quantity')).order_by('-qty')[:7]
    )
    top_prod_labels = [item['product_name'] or 'Unknown' for item in top_products_qs]
    top_prod_counts = [int(item['qty'] or 0) for item in top_products_qs]

    # Top selling products (for template list)
    top_products_list = (
        OrderItem.objects.values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

    # Low selling products (ascending by sold qty) as list of (id, {name, sold})
    low_sales_qs = (
        OrderItem.objects.values('product_id', 'product__name')
        .annotate(sold=Sum('quantity'))
        .order_by('sold')[:10]
    )
    low_selling = []
    for row in low_sales_qs:
        pid = row.get('product_id')
        low_selling.append((pid, {
            'name': row.get('product__name') or 'Unknown',
            'sold': int(row.get('sold') or 0),
        }))

    # KPI aliases used by admin_dashboard.html
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    total_revenue = sum(revenue_values) if revenue_values else 0

    context = {
        'kpi_total_products': total_products,
        'kpi_total_orders': total_orders,
        'kpi_paid_orders': Order.objects.filter(status='paid').count(),
        'kpi_customers': total_customers,

        # Aliases matching template variables
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,

        # Lists for template sections
        'top_products': top_products_list,
        'low_selling': low_selling,

        'orders_labels': orders_labels,
        'orders_counts': orders_counts,
        'revenue_labels': revenue_labels,
        'revenue_values': revenue_values,
        'top_cat_labels': top_cat_labels,
        'top_cat_counts': top_cat_counts,

        'status_labels': status_labels,
        'status_counts': status_counts,
        'coupon_labels': coupon_labels,
        'coupon_counts': coupon_counts,
        'top_prod_labels': top_prod_labels,
        'top_prod_counts': top_prod_counts,
    }
    return render(request, 'admin_dashboard.html', context)
