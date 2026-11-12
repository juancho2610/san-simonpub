#Modelo de las señales de bloqueos de inicio de sesion
cat > usuarios/senales.py <<'EOF'
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import seguridad

#Intentos de logeo fallidos y se rerquiere usuario activo
@receiver(user_login_failed)
def al_fallar_ingreso(sender, credentials, **kwargs):
    seguridad.registrar_fallo(credentials.get('username'))


@receiver(user_logged_in)
def al_ingresar(sender, request, user, **kwargs):
    seguridad.limpiar(user.get_username())
EOF

cat > usuarios/apps.py <<'EOF'
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        from . import senales  # noqa: F401  (conecta las señales)
