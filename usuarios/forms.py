#Formulario de registro
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Rol, Usuario

#Clase Registro para cliente desde formulario
class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    acepta_privacidad = forms.BooleanField(
        error_messages={'required': 'Debes aceptar la política de datos para crear tu cuenta.'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['acepta_privacidad'].label = format_html(
            'Acepto la <a href="{}" target="_blank" rel="noopener">política de '
            'tratamiento de datos</a> y autorizo el uso de mis datos para las '
            'finalidades que allí se describen.', reverse('privacidad'))

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'telefono')

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # El rol lo decide el servidor, nunca el navegador.
        usuario.rol = Rol.objects.get(codigo=Rol.CLIENTE)
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.acepto_privacidad_en = timezone.now()
        usuario.version_privacidad = settings.PRIVACIDAD_VERSION
        if commit:
            usuario.save()
        return usuario
