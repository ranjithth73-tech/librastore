"""
URLs for Custom Admin Views
"""
from django.urls import path
from . import admin_views

urlpatterns = [
    # Products
    path('products/', admin_views.admin_products_list, name='admin_products_list'),
    path('products/add/', admin_views.admin_product_add, name='admin_product_add'),
    path('products/<int:product_id>/edit/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('products/<int:product_id>/delete/', admin_views.admin_product_delete, name='admin_product_delete'),
    
    # Orders
    path('orders/', admin_views.admin_orders_list, name='admin_orders_list'),
    path('orders/<int:order_id>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/update/', admin_views.admin_order_update_status, name='admin_order_update_status'),
    
    # Customers
    path('customers/', admin_views.admin_customers_list, name='admin_customers_list'),
    path('customers/<int:customer_id>/', admin_views.admin_customer_detail, name='admin_customer_detail'),
    
    # Coupons
    path('coupons/', admin_views.admin_coupons_list, name='admin_coupons_list'),
    path('coupons/add/', admin_views.admin_coupon_add, name='admin_coupon_add'),
    path('coupons/<int:coupon_id>/edit/', admin_views.admin_coupon_edit, name='admin_coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', admin_views.admin_coupon_delete, name='admin_coupon_delete'),
    path('coupons/<int:coupon_id>/toggle/', admin_views.admin_coupon_toggle, name='admin_coupon_toggle'),
    
    # Categories
    path('categories/', admin_views.admin_categories_list, name='admin_categories_list'),
    path('categories/add/', admin_views.admin_category_add, name='admin_category_add'),
    path('categories/<int:category_id>/edit/', admin_views.admin_category_edit, name='admin_category_edit'),
    path('categories/<int:category_id>/delete/', admin_views.admin_category_delete, name='admin_category_delete'),
]
