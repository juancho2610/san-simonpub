#Formulario de registro
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Rol, Usuario

#Clase Registro para cliente desde formulario
class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'telefono')

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # El rol lo decide el servidor, nunca el navegador.
        usuario.rol = Rol.objects.get(codigo=Rol.CLIENTE)
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            usuario.save()
        return usuario
