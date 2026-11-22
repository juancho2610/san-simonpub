from django.core.management.base import BaseCommand

from musica.youtube import purgar_busquedas


class Command(BaseCommand):
    help = ('Borra las búsquedas de YouTube guardadas hace más de N días '
            '(la política de la API pide no conservar sus datos más de 30).')

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=7)

    def handle(self, *args, **opciones):
        borradas = purgar_busquedas(opciones['dias'])
        self.stdout.write(f'Búsquedas borradas: {borradas}')
