from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid

# Create your models here.

class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor')
    store_name = models.CharField(max_length=200, default='-')
    owner_name = models.CharField(max_length=100, default='unknown')
    phone = models.CharField(max_length=20, default='-')
    slug = models.SlugField(max_length=200, unique=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendors_logos/', blank=True, null=True)


    def __str__(self):
        return self.store_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.store_name)
            slug = base_slug
            while Vendor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            self.slug = slug
        super().save(*args, **kwargs)
    