from properties.models import Casa
from django.db import models


class TipoDispositivo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Dispositivo"
        verbose_name_plural = "Tipos de Dispositivos"


class DispositivoIoT(models.Model):
    casa = models.ForeignKey(
        Casa, on_delete=models.CASCADE, related_name="dispositivos"
    )
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoDispositivo, on_delete=models.PROTECT)
    ubicacion = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.casa}"

    class Meta:
        verbose_name = "Dispositivo IoT"
        verbose_name_plural = "Dispositivos IoT"
