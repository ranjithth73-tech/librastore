from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Customer


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_customer(sender, instance, created, **kwargs):
    """Create or update customer profile when user is saved."""
    if created:
        Customer.objects.create(user=instance, name=instance.username, email=instance.email)
    else:
        # Only save customer if it exists
        if hasattr(instance, 'customer'):
            instance.customer.name = instance.username
            instance.customer.email = instance.email
            instance.customer.save()