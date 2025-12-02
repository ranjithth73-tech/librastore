from . import views
from django.urls import path

urlpatterns = [
    path('',views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/category/<slug:slug>/', views.category_shop, name='category_shop'),
    path('product/<int:pk>/', views.product_details_by_id, name='product_details_by_id'),
    path('product/<slug:slug>/', views.product_details, name='product_details'),
    path('checkout/',views.checkout,name='checkout'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('order-success/', views.order_success,name = 'order_success'),
    path('about', views.about_view, name='about'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Stripe 
    # path('create-checkout-session',views.)
    
]


