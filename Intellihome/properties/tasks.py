from django.utils import timezone
from .models import Reserva, ConfiguracionTiempoSimulado
from django.core.mail import send_mail

def limpiar_reservas_temporales():
    tiempo_limite = timezone.now() - timezone.timedelta(minutes=5)
    
    reservas_expiradas = Reserva.objects.filter(
        estado__in=['TEMPORAL', 'CONFIRMADA'],
        fecha_ultimo_pago__lt=tiempo_limite
    ).exclude(estado__in=['PAGADA', 'NO_PAGADO'])
    
    for reserva in reservas_expiradas:
        casa = reserva.casa
        casa.disponible = True
        casa.save()
        reserva.estado = 'NO_PAGADO'
        reserva.save()

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
