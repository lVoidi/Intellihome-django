from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class SystemStatus(models.Model):
    is_enabled = models.BooleanField(default=True, verbose_name="Sistema Habilitado")
    disabled_message = models.CharField(
        max_length=255,
        default="El sistema está temporalmente deshabilitado",
        verbose_name="Mensaje cuando está deshabilitado"
    )
    modified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='system_modifications',
        verbose_name="Modificado por"
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        verbose_name = "Estado del Sistema"
        verbose_name_plural = "Estado del Sistema"

    def __str__(self):
        return f"Sistema {'Habilitado' if self.is_enabled else 'Deshabilitado'}"

    def save(self, *args, **kwargs):
        if not SystemStatus.objects.exists() or self.pk:
            super().save(*args, **kwargs)
