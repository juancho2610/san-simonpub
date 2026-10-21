#menu de ejemplo
from decimal import Decimal

from django.core.management.base import BaseCommand

from menu.models import Categoria, Producto

# Datos INVENTADOS, solo para pruebas. Se reemplazan con el menú real.
MENU = {
    'Entradas': (1, [
        ('Nachos con queso', 'Totopos con queso fundido y guacamole', '18000'),
        ('Alitas BBQ', '8 alitas con salsa BBQ', '22000'),
        ('Papas criollas', 'Porción con salsa de la casa', '12000'),
    ]),
    'Platos fuertes': (2, [
        ('Hamburguesa de la casa', 'Carne, queso, tocineta y papas', '28000'),
        ('Picada para dos', 'Chorizo, chicharrón, yuca y arepa', '45000'),
    ]),
    'Cervezas': (3, [
        ('Cerveza nacional', 'Botella 330 ml', '6000'),
        ('Cerveza importada', 'Botella 330 ml', '12000'),
    ]),
    'Licores': (4, [
        ('Aguardiente (media)', 'Botella de 375 ml', '55000'),
        ('Whisky (copa)', 'Copa sencilla', '16000'),
    ]),
    'Bebidas naturales': (5, [
        ('Limonada natural', 'Vaso grande', '7000'),
        ('Jugo de mora', 'En agua o en leche', '8000'),
    ]),
}


class Command(BaseCommand):
    help = 'Carga categorías y productos de EJEMPLO (no usar en producción).'

    def handle(self, *args, **options):
        nuevos = 0
        for nombre_cat, (orden, productos) in MENU.items():
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre_cat, defaults={'orden': orden})
            for nombre, descripcion, precio in productos:
                _, creado = Producto.objects.get_or_create(
                    categoria=categoria, nombre=nombre,
                    defaults={'descripcion': descripcion,
                              'precio': Decimal(precio)})
                nuevos += creado
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {nuevos} productos nuevos creados.'))
