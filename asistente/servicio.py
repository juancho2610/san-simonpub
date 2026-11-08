#Modelo de los limites y registros
from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from usuarios.models import Usuario

from . import ia
from .models import Interaccion


class LimiteAlcanzado(Exception):
    """El cliente o el sistema llegó al tope diario de mensajes."""


MENSAJE_FALLO = (
    'En este momento no puedo responder con inteligencia artificial. '
    'Puedes usar los botones de temas o preguntarle al personal.')


def _inicio_dia():
    return timezone.make_aware(datetime.combine(timezone.localdate(), time.min))


def _mensajes_libres(**filtros):
    # Solo cuentan las preguntas escritas, no los botones de temas.
    return (Interaccion.objects.filter(creada__gte=_inicio_dia(), **filtros)
            .exclude(pregunta='').count())


def usados_hoy(usuario):
    return _mensajes_libres(usuario=usuario)


def preguntar(usuario, mensaje, historial):
    """Devuelve (texto, usó_ia, mensajes_restantes)."""
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
        return MENSAJE_FALLO, False, restantes

    registro.origen = Interaccion.Origen.IA
    registro.respuesta = texto
    registro.tokens_entrada = entrada
    registro.tokens_salida = salida
    registro.save(update_fields=[
        'origen', 'respuesta', 'tokens_entrada', 'tokens_salida'])
    return texto, True, restantes

