from django.conf import settings
from django.core.checks import Tags, Warning, register

PRUEBA = ('1x0000', '2x0000', '3x0000')


@register(Tags.security, deploy=True)
def revisar_produccion(app_configs, **kwargs):
    avisos = []
    if not settings.CAPTCHA_ACTIVO:
        avisos.append(Warning(
            'El captcha está desactivado (CAPTCHA_ACTIVO=False).',
            hint='Es solo una salida de emergencia: vuelve a activarlo.',
            id='geas.W001'))
    elif (settings.TURNSTILE_SITEKEY.startswith(PRUEBA)
          or settings.TURNSTILE_SECRET_KEY.startswith(PRUEBA)):
        avisos.append(Warning(
            'El captcha usa llaves de prueba: aprueban cualquier token.',
            hint='Crea el widget en Cloudflare y usa las llaves reales.',
            id='geas.W002'))
    elif not settings.TURNSTILE_SECRET_KEY:
        avisos.append(Warning(
            'Falta la clave secreta de Turnstile.', id='geas.W003'))
    if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
        avisos.append(Warning(
            'El correo usa el modo de consola: no se envía nada.',
            hint='Configura un servicio de envío real.', id='geas.W004'))
    if settings.RECUPERAR_ENLACE_EN_PANTALLA:
        avisos.append(Warning(
            'RECUPERAR_ENLACE_EN_PANTALLA está en True.',
            hint='Debe ser False en producción.', id='geas.W005'))
    return avisos
