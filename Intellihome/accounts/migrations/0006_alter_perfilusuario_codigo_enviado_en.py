# Generated by Django 5.1.2 on 2024-10-23 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_perfilusuario_codigo_enviado_en_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfilusuario',
            name='codigo_enviado_en',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
