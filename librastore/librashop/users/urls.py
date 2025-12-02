from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout, name='logout'),
    path('order-history/', views.order_history, name='order_history'),
    path('profile/', views.user_profile, name='profile'),
    path('orders/', views.my_orders, name='orders'),
    path('orders/status/', views.my_orders_status, name='my_orders_status'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('contact/', views.contact, name='contact'),
    path('debug-orders/', views.debug_orders, name='debug_orders'),
]
