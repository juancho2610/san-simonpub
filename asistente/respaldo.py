from django.conf import settings
from django.db.models import Count, Q
from django.urls import reverse

from cuentas.models import MetodoPago
from menu.models import Categoria

TEMAS = {
    'menu': 'Ver el menú',
    'pedir': 'Cómo hago un pedido',
    'musica': 'Cómo pido una canción',
    'pagar': 'Cómo pago',
    'horario': 'Horario y contacto',
}


def _menu():
    categorias = (
        Categoria.objects.filter(activa=True)
        .annotate(n=Count('productos', filter=Q(productos__disponible=True)))
        .filter(n__gt=0))
    if not categorias:
        return 'El menú no está disponible en este momento.', None
    lista = ', '.join(f'{c.nombre} ({c.n})' for c in categorias)
    texto = (f'Tenemos estas categorías: {lista}. '
             'En el menú ves la descripción y el precio de cada producto.')
    return texto, ('menu', 'Abrir el menú')


def _pedir():
    texto = ('1) Entra al menú y toca "Agregar" en lo que quieras. '
             '2) Abre el carrito y toca "Confirmar pedido"; si no tienes '
             'sesión, te pedimos ingresar o crear una cuenta. '
             '3) Elige si lo quieres en mesa (con el número de tu mesa), '
             'para recoger o a domicilio. '
             '4) Sigue el estado de tu pedido en la sección Pedidos.')
    return texto, ('ver_carrito', 'Ir al carrito')


def _musica():
    texto = (f'Para pedir canciones necesitas un pedido en mesa de las últimas '
             f'{settings.MUSICA_VENTANA_PEDIDO_HORAS} horas. Puedes tener hasta '
             f'{settings.MUSICA_MAX_EN_COLA_POR_CLIENTE} canciones en la cola. '
             'Entra a Música, busca la canción y toca "Pedir".')
    return texto, ('catalogo_musical', 'Ir a Música')


def _pagar():
    metodos = list(MetodoPago.objects.filter(activo=True)
                   .values_list('nombre', flat=True))
    medios = ', '.join(metodos) if metodos else 'los medios que tenga el local'
    texto = ('Cuando quieras pagar, pide la cuenta al personal. '
             f'Puedes pagar con: {medios}. Si son varias personas, avísenle '
             'al personal para dividir el pago.')
    return texto, None


def _horario():
    negocio = settings.NEGOCIO
    partes = [f"Horario: {negocio['horario']}."]
    if negocio.get('direccion'):
        partes.append(f"Dirección: {negocio['direccion']}.")
    if negocio.get('telefono'):
        partes.append(f"Teléfono: {negocio['telefono']}.")
    return ' '.join(partes), None


_RESPUESTAS = {
    'menu': _menu, 'pedir': _pedir, 'musica': _musica,
    'pagar': _pagar, 'horario': _horario,
}


def responder(tema):
    """Devuelve {'texto', 'enlace'} o None si el tema no existe."""
    funcion = _RESPUESTAS.get(tema)
    if funcion is None:
        return None
    texto, enlace = funcion()
    if enlace:
        enlace = {'url': reverse(enlace[0]), 'etiqueta': enlace[1]}
    return {'texto': texto, 'enlace': enlace}
