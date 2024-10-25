from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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

class AdminPasswordStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_password_change = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Estado de Contraseña de Admin"
        verbose_name_plural = "Estados de Contraseña de Admin"

class TipoTransporte(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class EstiloCasa(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_nacimiento = models.DateField()
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    incluir_pago = models.BooleanField(default=False)
    estilos_casa = models.ManyToManyField(EstiloCasa)
    tipos_transporte = models.ManyToManyField(TipoTransporte)
    email_verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=6, null=True, blank=True)
    codigo_enviado_en = models.DateTimeField(auto_now_add=True)
    intentos_verificacion = models.IntegerField(default=0)
    ultimo_codigo_enviado = models.DateTimeField(null=True, blank=True)
    # Nuevos campos para el pago
    nombre_tarjetahabiente = models.CharField(max_length=100, blank=True, null=True)
    numero_tarjeta = models.CharField(max_length=16, blank=True, null=True)
    fecha_validez = models.DateField(blank=True, null=True)
    numero_verificador = models.CharField(max_length=4, blank=True, null=True)
    marca_tarjeta = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_user_status(self):
        if self.user.is_superuser:
            return 'Administrador Principal'
        elif self.user.is_staff:
            try:
                promocion = PromocionAdministrador.objects.filter(
                    usuario=self.user,
                    estado='aceptada'
                ).latest('fecha_solicitud')
                return 'Administrador Promovido'
            except PromocionAdministrador.DoesNotExist:
                if self.user.is_staff:
                    return 'Administrador Promovido'
        return 'Usuario Normal'

class PromocionAdministrador(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promociones')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    codigo_confirmacion = models.CharField(max_length=6)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada')
    ], default='pendiente')
    
    def __str__(self):
        return f"Promoción de {self.usuario.username}"
