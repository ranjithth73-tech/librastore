"""
URL configuration for librashop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from store import admin_views as admin_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/', include('store.admin_urls')),  # Custom admin interface
    path('',include('store.urls')),
    path('cart/', include('cart.urls')),
    path('accounts/',include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('transaction/', include('transaction.urls')),
    path('coupons/', include('coupons.urls')),
    path('vendors/', include('vendors.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
