from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import seguridad


@receiver(user_login_failed)
def al_fallar_ingreso(sender, credentials, **kwargs):
    seguridad.registrar_fallo(credentials.get('username'))


@receiver(user_logged_in)
def al_ingresar(sender, request, user, **kwargs):
    seguridad.limpiar(user.get_username())
