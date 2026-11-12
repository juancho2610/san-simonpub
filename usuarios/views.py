from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from . import captcha, seguridad
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
        if not captcha.verificar(request):
            form.add_error(None, captcha.MENSAJE)
        elif form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('inicio')
    else:
        form = RegistroClienteForm()
    return render(request, 'usuarios/registro.html', {'form': form})


class LoginConCaptcha(auth_views.LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if not captcha.verificar(request):
            form = self.get_form()
            form.add_error(None, captcha.MENSAJE)
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)


class RecuperarConCaptcha(auth_views.PasswordResetView):
    template_name = 'usuarios/password_reset_form.html'
    email_template_name = 'usuarios/password_reset_email.txt'
    subject_template_name = 'usuarios/password_reset_asunto.txt'
    success_url = reverse_lazy('password_reset_done')

    def post(self, request, *args, **kwargs):
        if not captcha.verificar(request):
            form = self.get_form()
            form.add_error(None, captcha.MENSAJE)
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)


def inicio(request):
    if not request.user.is_authenticated:
        return render(request, 'usuarios/inicio.html',
                      {'negocio': settings.NEGOCIO})
    destinos = {
        Rol.ADMIN: 'panel_admin',
        Rol.SERVICIO: 'panel_servicio',
        Rol.COCINA_BAR: 'panel_cocina',
        Rol.CLIENTE: 'panel_cliente',
    }
    codigo = request.user.rol.codigo if request.user.rol else Rol.CLIENTE
    return redirect(destinos[codigo])


def _panel(request, titulo, extra=None):
    contexto = {'titulo': titulo}
    if extra:
        contexto.update(extra)
    return render(request, 'usuarios/panel.html', contexto)


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
    from cuentas.models import Cuenta  # importación local: evita ciclos
    pendientes = Cuenta.objects.filter(
        cliente=request.user, estado=Cuenta.Estado.PENDIENTE)
    saldo = sum((c.saldo for c in pendientes), Decimal('0'))
    extra = {'saldo_pendiente': saldo} if saldo > 0 else {}
    return _panel(request, 'Bienvenido a San Simón Pub', extra)


class LoginProtegido(LoginConCaptcha):
    """Ingreso con captcha y límite de intentos fallidos."""

    def post(self, request, *args, **kwargs):
        if seguridad.bloqueado(request.POST.get('username', '')):
            form = self.get_form()
            form.add_error(None, seguridad.MENSAJE_BLOQUEO)
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)
