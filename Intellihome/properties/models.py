from django.db import models
from django.contrib.auth.models import User
from accounts.models import EstiloCasa

# Create your models here.

class ConfiguracionFotos(models.Model):
    cantidad_minima = models.PositiveIntegerField(default=3)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Fotos"
        verbose_name_plural = "Configuraciones de Fotos"

class Casa(models.Model):
    administrador = models.ForeignKey(User, on_delete=models.CASCADE)
    estilo = models.ForeignKey(EstiloCasa, on_delete=models.PROTECT)
    capacidad = models.PositiveIntegerField()
    habitaciones = models.PositiveIntegerField()
    banos = models.PositiveIntegerField()
    amenidades = models.TextField(
        help_text="Lista de amenidades separadas por comas",
        default="Sin amenidades"
    )
    caracteristicas = models.TextField()
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Casa {self.id} - {self.estilo.nombre}"

class FotoCasa(models.Model):
    casa = models.ForeignKey(Casa, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='casas/')
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ['orden']
