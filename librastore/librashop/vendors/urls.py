from django.urls import path
from . import views
from .views import ProductCreateView, ProductUpdateView, ProductDeleteView
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('orders/', views.vendor_orders, name='vendor_orders'),
    path('products/', views.vendor_products, name='vendor_products'),
    path('products/add/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('register/',views.vendor_registration, name='vendor_registration'),
    path('login/', auth_views.LoginView.as_view(template_name='vendor_login.html'), name='vendor_login'),
    # path('login/', views.vandor_login, name='vendor_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='vendor_logout'),
    path('settings/', views.vendor_settings, name='vendor_settings'),
]
