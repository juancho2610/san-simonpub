from datetime import timedelta

from django.conf import settings
from django.utils import timezone

CLAVE = 'mesa_qr'
HORAS = 6


def fijar(request, numero):
    vence = timezone.now() + timedelta(hours=HORAS)
    request.session[CLAVE] = {'n': numero, 'hasta': vence.timestamp()}


def actual(request):
    """La mesa recordada, o None si no hay, venció o ya no es válida."""
    dato = request.session.get(CLAVE)
    if dato is None:
        return None
    try:
        numero, hasta = int(dato['n']), float(dato['hasta'])
    except (KeyError, TypeError, ValueError):
        request.session.pop(CLAVE, None)
        return None
    if hasta < timezone.now().timestamp() or not 1 <= numero <= settings.MESAS_TOTAL:
        request.session.pop(CLAVE, None)
        return None
    return numero


def olvidar(request):
    request.session.pop(CLAVE, None)
