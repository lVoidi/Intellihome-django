from django.core.management.base import BaseCommand
from accounts.models import SystemStatus

class Command(BaseCommand):
    help = 'Inicializa la configuración del sistema'

    def handle(self, *args, **kwargs):
        if not SystemStatus.objects.exists():
            SystemStatus.objects.create()
            self.stdout.write(
                self.style.SUCCESS('Configuración del sistema inicializada exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING('La configuración del sistema ya existe')
            )