from django.core.management.base import BaseCommand

from usuarios import seguridad


class Command(BaseCommand):
    help = 'Borra los intentos de ingreso fallidos que ya vencieron.'

    def handle(self, *args, **options):
        borrados = seguridad.purgar_viejos()
        self.stdout.write(self.style.SUCCESS(f'Intentos borrados: {borrados}'))
