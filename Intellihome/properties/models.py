from django.db import models
from django.contrib.auth.models import User
from accounts.models import EstiloCasa
from django.utils import timezone

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
    disponible = models.BooleanField(default=False)
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto mensual con servicios incluidos",
        default=1.00 
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Casa {self.id} - {self.estilo.nombre}"

    def tiene_dispositivos_activos(self):
        return self.dispositivoiot_set.filter(estado=True).exists()
    
    @property
    def monto_sin_servicios(self):
        return float(self.monto) * 0.92  # 92% del monto original

    @property
    def monto_diario(self):
        return float(self.monto) / 30  # Monto mensual dividido entre 30 días

class FotoCasa(models.Model):
    casa = models.ForeignKey(Casa, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='casas/')
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ['orden']

class ConfiguracionTiempoSimulado(models.Model):
    minutos_por_mes = models.PositiveIntegerField(default=5)
    minutos_reserva_temporal = models.PositiveIntegerField(default=5)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Tiempo Simulado"
        verbose_name_plural = "Configuraciones de Tiempo Simulado"

    @property
    def minutos_por_dia(self):
        return self.minutos_por_mes / 30

class Reserva(models.Model):
    casa = models.ForeignKey(Casa, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)  # Permitimos que sea null
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('TEMPORAL', 'Temporal'),
            ('CONFIRMADA', 'Confirmada'),
            ('CANCELADA', 'Cancelada'),
        ],
        default='TEMPORAL'
    )
    es_indefinida = models.BooleanField(default=False)
    proximo_pago = models.DateField(null=True, blank=True)
    tipo_pago_actual = models.CharField(
        max_length=20,
        choices=[
            ('COMPLETO', 'Pago Completo'),
            ('SEMANAL', 'Pago Semanal'),
            ('DIARIO', 'Pago Diario'),
        ],
        default='COMPLETO'
    )
    cuotas_pagadas = models.IntegerField(default=0)
    cuotas_totales = models.IntegerField(default=1)
    historial_pagos = models.JSONField(default=list)
    tiempo_restante_minutos = models.FloatField(default=5.0)  # Inicialmente 5 minutos

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'Reserva de {self.casa.estilo.nombre} por {self.usuario.get_full_name()}'

    def esta_expirada(self):
        if self.estado != 'TEMPORAL':
            return False
        
        config = ConfiguracionTiempoSimulado.objects.first()
        if not config:
            minutos_limite = 5
        else:
            minutos_limite = config.minutos_reserva_temporal

        tiempo_transcurrido = timezone.now() - self.fecha_reserva
        return tiempo_transcurrido.total_seconds() / 60 > minutos_limite

    @property
    def dias_hasta_proximo_pago(self):
        if not self.proximo_pago:
            return 0
        dias = (self.proximo_pago - timezone.now().date()).days
        return dias

    @property
    def esta_vencida(self):
        return self.dias_hasta_proximo_pago < -5

    @property
    def minutos_hasta_proximo_pago(self):
        if not self.proximo_pago:
            return float('inf')
        
        # Convertir días a minutos (1 mes = 5 minutos)
        dias_reales = (self.proximo_pago - timezone.now().date()).days
        # 30 días = 5 minutos, entonces 1 día = 5/30 minutos
        return (dias_reales * 5) / 30

    @property
    def estado_pago(self):
        minutos = self.minutos_hasta_proximo_pago
        if minutos <= 0:
            return 'VENCIDO'
        elif minutos <= 1:  # Menos de 1 minuto (equivalente a 6 días reales)
            return 'URGENTE'
        elif minutos <= 2:  # Menos de 2 minutos (equivalente a 12 días reales)
            return 'PRÓXIMO'
        return 'AL_DIA'
