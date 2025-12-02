from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Vendor
from store.models import Product, Order, OrderItem, Category  # type: ignore
from .forms import ProductForm, CombinedRegistrationForm, VendorSettingsForm
from django.db import transaction
from django.db.models import Sum, Avg, Count, F, ExpressionWrapper, DecimalField
from django.contrib.auth import login
from django.utils.text import slugify

# Create your views here.


@login_required
def vendor_dashboard(request):
    if not hasattr(request.user, 'vendor'):
        messages.warning(request, 'You are not registered as a vendor!')
        return redirect('home')

    vendor = request.user.vendor
    products = Product.objects.filter(vendor=vendor)
    total_products = products.count()

    vendor_order_items = OrderItem.objects.filter(
        product__in=products
    ).select_related('product', 'order')

    # total_earnings = vendor_order_items.filter(order__status='paid').aggregate(total=Sum('price'))['total'] or 0
    # total_orders = vendor_order_items.filter(order__status='paid').aggregate(total=Count('order',distinct=True))['total'] or 0

    # recent_orders = Order.objects.filter(id__in=vendor_order_items.filter(order__status='paid').values('order_id')).order_by('-created_at').distinct()[:5]

    total_earnings = vendor_order_items.filter(order__status='paid').aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__price'),
                output_field=DecimalField()
                )
            )
        )['total'] or 0
    total_orders = vendor_order_items.filter(order__status='paid').aggregate(total=Count('order', distinct=True))['total'] or 0
    recent_orders = Order.objects.filter(  # type: ignore
        id__in=vendor_order_items.filter(order__status='paid').values('order_id')
    ).order_by('-date_odered').distinct()[:5]

    avg_rating_query = products.aggregate(avg_rating=Avg('reviews__rating'))['avg_rating']
    avg_rating = round(avg_rating_query, 1) if avg_rating_query else 'N/A'

    context = {
        'vendor': vendor,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_earnings': total_earnings,
        'avg_rating': avg_rating,
        'recent_orders': recent_orders,
        'products': products,
    }
    return render(request, 'dashboard.html', context)


@login_required
def vendor_orders(request):
    if not hasattr(request.user, 'vendor'):
        messages.warning(request, 'You are not registered as a vendor!')
        return redirect('home')

    vendor = request.user.vendor
    products = Product.objects.filter(vendor=vendor)  # type: ignore
    
    # Optimize query with select_related to avoid N+1
    vendor_order_items = OrderItem.objects.filter(
        product__in=products
    ).select_related('product', 'order')  # type: ignore

    # Get all unique orders for this vendor with prefetch
    from django.db.models import Prefetch
    orders = Order.objects.filter(  # type: ignore
        id__in=vendor_order_items.values('order_id')
    ).prefetch_related(
        Prefetch('orderitem_set', queryset=vendor_order_items)
    ).order_by('-date_odered').distinct()

    # Get order items with product info for each order
    orders_with_items = []
    for order in orders:
        # Use prefetched data instead of querying again
        items = [item for item in order.orderitem_set.all() if item.product in products]
        order_total = sum(item.quantity * item.product.price for item in items if item.product)
        orders_with_items.append({
            'order': order,
            'items': items,
            'total': order_total
        })

    context = {
        'vendor': vendor,
        'orders_with_items': orders_with_items,
        'total_orders': orders.count(),
    }
    return render(request, 'vendor_orders.html', context)


@login_required
def vendor_products(request):
    if not hasattr(request.user, 'vendor'):
        messages.warning(request, 'You are not registered as a vendor!')
        return redirect('home')

    vendor = request.user.vendor
    products = Product.objects.filter(vendor=vendor)

    context = {
        'vendor': vendor,
        'products': products,
    }
    return render(request, 'vendor_products.html', context)


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('vendor_dashboard')

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor
        # Set category from posted select
        category_id = self.request.POST.get('category')
        if category_id:
            try:
                form.instance.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(self.request, 'Selected category does not exist.')
                return self.form_invalid(form)
        # Set slug from name if missing
        if not getattr(form.instance, 'slug', None):
            form.instance.slug = slugify(form.instance.name)
        # Save image if provided
        image_file = self.request.FILES.get('image')
        if image_file:
            form.instance.image = image_file
        # Ensure available defaults to True if not set
        if form.instance.available is None:
            form.instance.available = True
        response = super().form_valid(form)
        messages.success(self.request, 'Product added successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('vendor_dashboard')

    def get_queryset(self):
        return self.request.user.vendor.products.all()

    def form_valid(self, form):
        # Allow updating category and image via the same template controls
        category_id = self.request.POST.get('category')
        if category_id:
            try:
                form.instance.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(self.request, 'Selected category does not exist.')
                return self.form_invalid(form)
        image_file = self.request.FILES.get('image')
        if image_file:
            form.instance.image = image_file
        if not getattr(form.instance, 'slug', None):
            form.instance.slug = slugify(form.instance.name)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('vendor_dashboard')

    def get_queryset(self):
        return self.request.user.vendor.products.all()

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully!')
        return super().delete(request, *args, **kwargs)


@transaction.atomic
def vendor_registration(request):
    if request.method == 'POST':
        form = CombinedRegistrationForm(request.POST, request.FILES)    
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # type: ignore
            login(request, user)
            messages.success(request, 'Your vendor account has been created successfully!')
            return redirect('vendor_dashboard')

        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CombinedRegistrationForm()

    return render(request, 'vendor_registration.html', {'form': form})


# def vandor_login(request):
#     return redirect(request, 'dashboard.html')


@login_required
def vendor_settings(request):
    """View for vendors to update their profile settings"""
    if not hasattr(request.user, 'vendor'):
        messages.warning(request, 'You are not registered as a vendor!')
        return redirect('home')
    
    vendor = request.user.vendor
    
    if request.method == 'POST':
        form = VendorSettingsForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated successfully!')
            return redirect('vendor_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VendorSettingsForm(instance=vendor)
    
    context = {
        'vendor': vendor,
        'form': form,
    }
    return render(request, 'vendor_settings.html', context)
