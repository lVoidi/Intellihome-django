# Generated by Django 5.1.2 on 2024-10-25 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0005_casa_monto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casa',
            name='monto',
            field=models.DecimalField(decimal_places=2, default=1.0, help_text='Monto mensual con servicios incluidos', max_digits=10),
        ),
    ]