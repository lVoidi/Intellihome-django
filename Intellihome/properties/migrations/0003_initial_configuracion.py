from django.db import migrations

def crear_configuracion_inicial(apps, schema_editor):
    ConfiguracionFotos = apps.get_model('properties', 'ConfiguracionFotos')
    if not ConfiguracionFotos.objects.exists():
        ConfiguracionFotos.objects.create(cantidad_minima=3)

class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0002_remove_casa_amenidades_delete_amenidad_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_configuracion_inicial),
    ]

