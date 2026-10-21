from pathlib import Path

import qrcode
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Genera el codigo QR que apunta al menu digital.'

    def add_arguments(self, parser):
        parser.add_argument(
            'url_base',
            help='Direccion base del sitio, ej: https://mi-dominio.com')

    def handle(self, *args, **options):
        url_base = options['url_base'].rstrip('/')
        if not url_base.startswith(('http://', 'https://')):
            raise CommandError('La direccion debe empezar con http:// o https://')

        destino = f'{url_base}/menu/'
        carpeta = Path(settings.BASE_DIR) / 'qr'
        carpeta.mkdir(exist_ok=True)
        archivo = carpeta / 'qr_menu.png'

        qrcode.make(destino).save(archivo)
        self.stdout.write(self.style.SUCCESS(f'QR creado en {archivo}'))
        self.stdout.write(f'Apunta a: {destino}')
