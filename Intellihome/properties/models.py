from django.db import models
from django.contrib.auth.models import User
from accounts.models import EstiloCasa
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

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
    ESTADOS = [
        ('DISPONIBLE', 'Disponible'),
        ('OCUPADA', 'Ocupada'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='DISPONIBLE'
    )

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
    TIPOS_PLAN = [
        ('DIARIO', 'Pago Diario'),
        ('MENSUAL_CON_SERVICIOS', 'Mensual con Servicios'),
        ('MENSUAL_SIN_SERVICIOS', 'Mensual sin Servicios'),
    ]

    ESTADOS = [
        ('TEMPORAL', 'Temporal'),
        ('CONFIRMADA', 'Confirmada'),
        ('PAGADA', 'Pagada'),
        ('NO_PAGADO', 'No Pagado')
    ]
    
    casa = models.ForeignKey('Casa', on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    fecha_inicio = models.DateField(null=True)
    fecha_fin = models.DateField(null=True)
    es_indefinida = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='TEMPORAL')
    tipo_plan = models.CharField(max_length=25, choices=TIPOS_PLAN, null=True, blank=True)
    cuotas_totales = models.IntegerField(default=0)
    cuotas_pagadas = models.IntegerField(default=0)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_pago = models.DateTimeField(null=True, blank=True)

    def calcular_monto_pago(self):
        if not self.tipo_plan:
            raise ValueError("Debe seleccionar un plan de pago primero")
        
        if self.tipo_plan == 'DIARIO':
            return self.casa.monto_diario
        elif self.tipo_plan == 'MENSUAL_CON_SERVICIOS':
            self.fecha_fin = self.fecha_inicio + timedelta(minutes=5)  # 5 minutos = 1 mes simulado
            return self.casa.monto
        else:  # MENSUAL_SIN_SERVICIOS
            self.fecha_fin = self.fecha_inicio + timedelta(minutes=5)  # 5 minutos = 1 mes simulado
            return self.casa.monto_sin_servicios
            
    def calcular_cuotas_totales(self):
        if not self.tipo_plan:
            return 0
            
        dias_totales = (self.fecha_fin - self.fecha_inicio).days
        
        if self.tipo_plan == 'DIARIO':
            return dias_totales
        else:  # Planes mensuales
            meses_completos = dias_totales // 30
            if dias_totales % 30 > 0:
                meses_completos += 1
            return meses_completos
        
    def tiempo_restante_pago(self):
        minutos_limite = 5  # 5 minutos representan un mes en tiempo simulado
        
        # Usar la fecha de último pago si existe, sino usar fecha_reserva
        ultima_fecha = self.fecha_ultimo_pago if self.fecha_ultimo_pago else self.fecha_reserva
        tiempo_transcurrido = timezone.now() - ultima_fecha
        tiempo_restante = minutos_limite - (tiempo_transcurrido.total_seconds() / 60)
        
        return max(0, tiempo_restante)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'Reserva de {self.casa.estilo.nombre} por {self.usuario.get_full_name()}'

    def esta_expirada(self):
        if self.estado not in ['PAGADA', 'CONFIRMADA']:
            return False
        
        minutos_limite = 5  # 5 minutos representan un mes en tiempo simulado
        ultima_fecha = self.fecha_ultimo_pago if self.fecha_ultimo_pago else self.fecha_reserva
        tiempo_transcurrido = timezone.now() - ultima_fecha
        
        if tiempo_transcurrido.total_seconds() / 60 > minutos_limite:
            self.estado = 'NO_PAGADO'
            self.casa.disponible = True
            self.casa.save()
            return True
        return False