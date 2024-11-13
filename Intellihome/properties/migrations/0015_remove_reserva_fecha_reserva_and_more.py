# Generated by Django 5.1.2 on 2024-10-28 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0014_casa_estado'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reserva',
            name='fecha_reserva',
        ),
        migrations.RemoveField(
            model_name='reserva',
            name='historial_pagos',
        ),
        migrations.RemoveField(
            model_name='reserva',
            name='proximo_pago',
        ),
        migrations.RemoveField(
            model_name='reserva',
            name='tiempo_restante_minutos',
        ),
        migrations.RemoveField(
            model_name='reserva',
            name='tipo_pago_actual',
        ),
        migrations.AddField(
            model_name='reserva',
            name='tipo_plan',
            field=models.CharField(blank=True, choices=[('DIARIO', 'Pago Diario'), ('MENSUAL_CON_SERVICIOS', 'Mensual con Servicios'), ('MENSUAL_SIN_SERVICIOS', 'Mensual sin Servicios')], max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='cuotas_totales',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='estado',
            field=models.CharField(default='CONFIRMADA', max_length=20),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='fecha_fin',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='fecha_inicio',
            field=models.DateField(null=True),
        ),
    ]
