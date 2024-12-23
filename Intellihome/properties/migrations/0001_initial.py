# Generated by Django 5.1.2 on 2024-10-25 07:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0008_perfilusuario_fecha_validez_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Amenidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Amenidades',
            },
        ),
        migrations.CreateModel(
            name='Casa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacidad', models.PositiveIntegerField()),
                ('habitaciones', models.PositiveIntegerField()),
                ('banos', models.PositiveIntegerField()),
                ('caracteristicas', models.TextField()),
                ('latitud', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitud', models.DecimalField(decimal_places=6, max_digits=9)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('administrador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('amenidades', models.ManyToManyField(to='properties.amenidad')),
                ('estilo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.estilocasa')),
            ],
        ),
        migrations.CreateModel(
            name='ConfiguracionFotos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_minima', models.PositiveIntegerField(default=3)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('modificado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Configuración de Fotos',
                'verbose_name_plural': 'Configuraciones de Fotos',
            },
        ),
        migrations.CreateModel(
            name='FotoCasa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='casas/')),
                ('orden', models.PositiveIntegerField(default=0)),
                ('casa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fotos', to='properties.casa')),
            ],
            options={
                'ordering': ['orden'],
            },
        ),
    ]
