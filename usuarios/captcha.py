import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

URL_VERIFICACION = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
MENSAJE = 'No pudimos verificar que eres una persona. Intenta de nuevo.'


def verificar(request):
    """True solo si Cloudflare confirma el token. Ante cualquier duda, rechaza."""
    if not settings.CAPTCHA_ACTIVO:
        return True
    secreto = settings.TURNSTILE_SECRET_KEY
    token = request.POST.get('cf-turnstile-response', '')
    if not secreto or not token or len(token) > 2048:
        return False
    datos = urllib.parse.urlencode({'secret': secreto, 'response': token}).encode()
    try:
        peticion = urllib.request.Request(URL_VERIFICACION, data=datos)
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            resultado = json.load(respuesta)
    except Exception:
        logger.exception('No se pudo contactar a Turnstile')
        return False
    if not resultado.get('success'):
        logger.warning('Turnstile rechazó el token: %s', resultado.get('error-codes'))
        return False
    return True
