# Generated by Django 5.1.2 on 2024-10-26 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0011_reserva_proximo_pago_alter_reserva_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='cuotas_pagadas',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='reserva',
            name='cuotas_totales',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='reserva',
            name='historial_pagos',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='reserva',
            name='tipo_pago_actual',
            field=models.CharField(choices=[('COMPLETO', 'Pago Completo'), ('SEMANAL', 'Pago Semanal'), ('DIARIO', 'Pago Diario')], default='COMPLETO', max_length=20),
        ),
    ]
