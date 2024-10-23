from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import AdminPasswordStatus

@receiver(user_logged_in)
def check_admin_password_status(sender, user, request, **kwargs):
    if user.is_staff:
        AdminPasswordStatus.objects.get_or_create(user=user)

@receiver(post_save, sender=User)
def update_password_change_time(sender, instance, **kwargs):
    if instance.is_staff:
        AdminPasswordStatus.objects.update_or_create(
            user=instance,
            defaults={'last_password_change': timezone.now()}
        )