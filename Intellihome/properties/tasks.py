from django.utils import timezone
from .models import Reserva, ConfiguracionTiempoSimulado
from django.core.mail import send_mail

def limpiar_reservas_temporales():
    config = ConfiguracionTiempoSimulado.objects.first()
    minutos_limite = config.minutos_reserva_temporal if config else 5

    tiempo_limite = timezone.now() - timezone.timedelta(minutes=minutos_limite)
    
    Reserva.objects.filter(
        estado='TEMPORAL',
        fecha_reserva__lt=tiempo_limite
    ).update(estado='CANCELADA')

def verificar_pagos_vencidos():
    reservas_vencidas = Reserva.objects.filter(
        estado='CONFIRMADA',
        proximo_pago__lt=timezone.now().date() - timezone.timedelta(days=5)
    )

    for reserva in reservas_vencidas:
        # Revocar acceso
        reserva.estado = 'CANCELADA'
        reserva.save()

        # Notificar al usuario
        mensaje = f"""
        Su reserva para la casa {reserva.casa.estilo.nombre} ha sido cancelada
        debido a falta de pago por más de 5 días.
        """
        
        send_mail(
            'Cancelación de Reserva por Falta de Pago - IntelliHome',
            mensaje,
            'noreply@intellihome.com',
            [reserva.usuario.email],
            fail_silently=True,
        )
