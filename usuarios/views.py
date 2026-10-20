#Vistas de usuarios
from functools import wraps

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import RegistroClienteForm
from .models import Rol


def rol_requerido(*codigos):
    """El guardia: solo deja pasar a los roles indicados."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            rol = request.user.rol
            if rol is None or rol.codigo not in codigos:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return login_required(envoltura)
    return decorador


def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    else:
        form = RegistroClienteForm()
    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
def inicio(request):
    destinos = {
        Rol.ADMIN: 'panel_admin',
        Rol.SERVICIO: 'panel_servicio',
        Rol.COCINA_BAR: 'panel_cocina',
        Rol.CLIENTE: 'panel_cliente',
    }
    codigo = request.user.rol.codigo if request.user.rol else Rol.CLIENTE
    return redirect(destinos[codigo])


def _panel(request, titulo):
    return render(request, 'usuarios/panel.html', {'titulo': titulo})


@rol_requerido(Rol.ADMIN)
def panel_admin(request):
    return _panel(request, 'Panel del Administrador')


@rol_requerido(Rol.SERVICIO)
def panel_servicio(request):
    return _panel(request, 'Panel de Personal de servicio')


@rol_requerido(Rol.COCINA_BAR)
def panel_cocina(request):
    return _panel(request, 'Panel de Cocina / Bar')


@rol_requerido(Rol.CLIENTE)
def panel_cliente(request):
    return _panel(request, 'Bienvenido a San Simón Pub')
