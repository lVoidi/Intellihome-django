from django.db import migrations
from django.utils import timezone

def calcular_cuotas_totales(fecha_inicio, fecha_fin, tipo_plan):
    dias_totales = (fecha_fin - fecha_inicio).days
    
    if tipo_plan == 'DIARIO':
        return dias_totales
    else:  # Planes mensuales
        meses_completos = dias_totales // 30
        if dias_totales % 30 > 0:
            meses_completos += 1
        return meses_completos

def set_default_values(apps, schema_editor):
    Reserva = apps.get_model('properties', 'Reserva')
    for reserva in Reserva.objects.all():
        if not reserva.fecha_inicio:
            reserva.fecha_inicio = timezone.now().date()
        if not reserva.fecha_fin:
            reserva.fecha_fin = timezone.now().date() + timezone.timedelta(days=30)
        if not reserva.tipo_plan:
            reserva.tipo_plan = 'MENSUAL_CON_SERVICIOS'
            reserva.cuotas_totales = calcular_cuotas_totales(
                reserva.fecha_inicio,
                reserva.fecha_fin,
                'MENSUAL_CON_SERVICIOS'
            )
        reserva.save()

class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0015_remove_reserva_fecha_reserva_and_more'),
    ]

    operations = [
        migrations.RunPython(set_default_values),
    ]