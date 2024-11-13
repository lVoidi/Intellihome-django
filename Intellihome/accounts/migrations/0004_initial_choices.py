from django.db import migrations

def crear_opciones_iniciales(apps, schema_editor):
    EstiloCasa = apps.get_model('accounts', 'EstiloCasa')
    TipoTransporte = apps.get_model('accounts', 'TipoTransporte')

    # Crear estilos de casa
    estilos_casa = [
        {'nombre': 'Playa', 'descripcion': 'Casa cerca del mar'},
        {'nombre': 'Montaña', 'descripcion': 'Casa en zona montañosa'},
        {'nombre': 'Ciudad', 'descripcion': 'Casa en zona urbana'},
    ]
    for estilo in estilos_casa:
        EstiloCasa.objects.create(**estilo)

    # Crear tipos de transporte
    transportes = ['Moto', 'Automóvil', 'Bicicleta']
    for transporte in transportes:
        TipoTransporte.objects.create(nombre=transporte)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_estilocasa_tipotransporte_perfilusuario'),
    ]

    operations = [
        migrations.RunPython(crear_opciones_iniciales),
    ]
