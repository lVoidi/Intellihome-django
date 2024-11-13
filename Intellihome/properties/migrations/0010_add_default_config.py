from django.db import migrations

def crear_configuracion_default(apps, schema_editor):
    ConfiguracionTiempoSimulado = apps.get_model('properties', 'ConfiguracionTiempoSimulado')
    if not ConfiguracionTiempoSimulado.objects.exists():
        ConfiguracionTiempoSimulado.objects.create(minutos_reserva_temporal=15)

class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0009_reserva_es_indefinida_reserva_estado_and_more'),  # Reemplaza con la migración anterior
    ]

    operations = [
        migrations.RunPython(crear_configuracion_default),
    ]
