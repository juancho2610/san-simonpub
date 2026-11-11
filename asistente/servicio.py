#Modelo de los limites y registros
import re
from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from menu.models import Producto
from usuarios.models import Usuario

from . import ia
from .models import Interaccion


class LimiteAlcanzado(Exception):
    """El cliente o el sistema llegó al tope diario de mensajes."""


MENSAJE_FALLO = (
    'En este momento no puedo responder con inteligencia artificial. '
    'Puedes usar los botones de temas o preguntarle al personal.')
MENSAJE_SOLO_PRODUCTOS = 'Estas opciones del menú podrían gustarte:'
MAX_SUGERIDOS = 3
_PATRON = re.compile(r'\[\[\s*PRODUCTOS\s*:\s*([\d\s,]*)\]\]', re.IGNORECASE)


def _inicio_dia():
    return timezone.make_aware(datetime.combine(timezone.localdate(), time.min))


def _mensajes_libres(**filtros):
    # Solo cuentan las preguntas escritas, no los botones de temas.
    return (Interaccion.objects.filter(creada__gte=_inicio_dia(), **filtros)
            .exclude(pregunta='').count())


def usados_hoy(usuario):
    return _mensajes_libres(usuario=usuario)


def _pesos(valor):
    return '$' + f'{valor:,.0f}'.replace(',', '.')


def _separar_productos(texto):
    """Quita el código [[PRODUCTOS: ...]] del texto y devuelve sus números."""
    ids = []
    for grupo in _PATRON.findall(texto):
        for trozo in grupo.split(','):
            trozo = trozo.strip()
            if trozo.isascii() and trozo.isdigit() and int(trozo) not in ids:
                ids.append(int(trozo))
    limpio = re.sub(r'\n{3,}', '\n\n', _PATRON.sub('', texto)).strip()
    return limpio, ids[:MAX_SUGERIDOS]


def _productos_validos(ids):
    """Solo productos reales y disponibles; nombre y precio salen de la base."""
    if not ids:
        return []
    por_id = {p.pk: p for p in Producto.objects.filter(
        pk__in=ids, disponible=True, categoria__activa=True)}
    resultado = []
    for pk in ids:
        producto = por_id.get(pk)
        if producto is not None:
            resultado.append({
                'id': producto.pk,
                'nombre': producto.nombre,
                'precio': _pesos(producto.precio),
                'url': reverse('agregar_al_carrito', args=[producto.pk]),
            })
    return resultado


def preguntar(usuario, mensaje, historial):
    """Devuelve (texto, usó_ia, mensajes_restantes, productos_sugeridos)."""
    maximo = settings.ASISTENTE_MAX_MENSAJES_DIA
    with transaction.atomic():
        # Bloquear al cliente evita que mensajes simultáneos se salten el tope.
        Usuario.objects.select_for_update().get(pk=usuario.pk)
        usados = usados_hoy(usuario)
        if usados >= maximo:
            raise LimiteAlcanzado('personal')
        if _mensajes_libres() >= settings.ASISTENTE_MAX_MENSAJES_GLOBAL_DIA:
            raise LimiteAlcanzado('global')
        # Se reserva el cupo ANTES de llamar a la IA (la llamada es lenta).
        registro = Interaccion.objects.create(
            usuario=usuario, tema='libre', pregunta=mensaje,
            origen=Interaccion.Origen.RESPALDO)
    restantes = maximo - usados - 1

    try:
        texto, entrada, salida = ia.responder(historial, mensaje)
    except ia.ErrorIA:
        registro.respuesta = MENSAJE_FALLO
        registro.save(update_fields=['respuesta'])
        return MENSAJE_FALLO, False, restantes, []

    texto, ids = _separar_productos(texto)
    productos = _productos_validos(ids)
    if not texto and productos:
        texto = MENSAJE_SOLO_PRODUCTOS
    if not texto:
        registro.respuesta = MENSAJE_FALLO
        registro.save(update_fields=['respuesta'])
        return MENSAJE_FALLO, False, restantes, []

    registro.origen = Interaccion.Origen.IA
    registro.respuesta = texto
    registro.tokens_entrada = entrada
    registro.tokens_salida = salida
    registro.save(update_fields=[
        'origen', 'respuesta', 'tokens_entrada', 'tokens_salida'])
    return texto, True, restantes, productos
