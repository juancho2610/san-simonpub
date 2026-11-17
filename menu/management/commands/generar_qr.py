from pathlib import Path

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H


def _rotulo(imagen, texto):
    """Agrega el texto debajo del QR, para que el personal sepa de qué mesa es."""
    base = imagen.convert('RGB')
    try:
        fuente = ImageFont.load_default(size=int(base.width * 0.09))
    except TypeError:
        fuente = ImageFont.load_default()
    alto = int(base.width * 0.16)
    lienzo = Image.new('RGB', (base.width, base.height + alto), 'white')
    lienzo.paste(base, (0, 0))
    dibujo = ImageDraw.Draw(lienzo)
    caja = dibujo.textbbox((0, 0), texto, font=fuente)
    x = (lienzo.width - (caja[2] - caja[0])) // 2
    y = base.height + (alto - (caja[3] - caja[1])) // 2 - caja[1]
    dibujo.text((x, y), texto, fill='black', font=fuente)
    return lienzo


class Command(BaseCommand):
    help = 'Genera el QR del menú y, con --mesas, un QR por cada mesa.'

    def add_arguments(self, parser):
        parser.add_argument('url_base', help='Ej: https://sansimonpub.com')
        parser.add_argument('--mesas', action='store_true',
                            help='Genera un QR por mesa (de 1 a MESAS_TOTAL)')

    def _guardar(self, destino, carpeta, nombre, rotulo=None):
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=20, border=4)
        qr.add_data(destino)
        qr.make(fit=True)
        imagen = qr.make_image(fill_color='black', back_color='white').get_image()
        if rotulo:
            imagen = _rotulo(imagen, rotulo)
        imagen.save(carpeta / f'{nombre}.png')
        qrcode.make(destino, image_factory=qrcode.image.svg.SvgPathImage,
                    error_correction=ERROR_CORRECT_H, border=4
                    ).save(str(carpeta / f'{nombre}.svg'))

    def handle(self, *args, **options):
        base = options['url_base'].rstrip('/')
        if not base.startswith(('http://', 'https://')):
            raise CommandError('La dirección debe empezar con http:// o https://')
        carpeta = Path(settings.BASE_DIR) / 'qr'
        carpeta.mkdir(exist_ok=True)

        self._guardar(f'{base}/menu/', carpeta, 'qr_menu')
        self.stdout.write(f'Menú: {base}/menu/')
        if options['mesas']:
            for n in range(1, settings.MESAS_TOTAL + 1):
                self._guardar(f'{base}/mesa/{n}/', carpeta, f'mesa_{n:02d}', f'Mesa {n}')
            self.stdout.write(f'Mesas 1 a {settings.MESAS_TOTAL}: {base}/mesa/N/')
        self.stdout.write(self.style.SUCCESS(f'Archivos en {carpeta}'))
