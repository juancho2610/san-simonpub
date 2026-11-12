#Modo de seguridad para inicios de sesion no deseados
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import IntentoIngreso

#Funcion para bloqueos de sesion segun intentos fallidos
MENSAJE_BLOQUEO = ('Demasiados intentos fallidos. Espera unos minutos e '
                   'inténtalo de nuevo, o recupera tu contraseña.')


def _clave(nombre):
    return (nombre or '').strip().lower()[:150]


def _desde():
    return timezone.now() - timedelta(minutes=settings.LOGIN_VENTANA_MIN)


def bloqueado(nombre):
    clave = _clave(nombre)
    if not clave:
        return False
    recientes = IntentoIngreso.objects.filter(nombre=clave, creado__gte=_desde())
    return recientes.count() >= settings.LOGIN_MAX_INTENTOS


def registrar_fallo(nombre):
    clave = _clave(nombre)
    if clave:
        IntentoIngreso.objects.create(nombre=clave)


def limpiar(nombre):
    IntentoIngreso.objects.filter(nombre=_clave(nombre)).delete()


def purgar_viejos():
    return IntentoIngreso.objects.filter(creado__lt=_desde()).delete()[0]
