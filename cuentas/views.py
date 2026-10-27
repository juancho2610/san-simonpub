# Configuracion de la vista para las cuentas de los clientes.
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from django.http import Http404

from pedidos.models import Pedido
from usuarios.models import Rol
from usuarios.views import rol_requerido

from .models import Cuenta, MetodoPago
from .services import CobroNoPermitido, cobrar_cuenta, dejar_pendiente

LINEAS = 4  # cuántos pagos se pueden anotar de una vez


def _parse_monto(texto):
    """Pesos enteros. Acepta 20000, 20.000, 20,000 o $20.000."""
    limpio = (texto.replace('$', '').replace('.', '')
              .replace(',', '').replace(' ', ''))
    if not (limpio.isascii() and limpio.isdigit()) or len(limpio) > 9:
        return None
    valor = Decimal(limpio)
    return valor if valor > 0 else None


def _leer_lineas(post):
    lineas = []
    for i in range(1, LINEAS + 1):
        metodo_id = post.get(f'metodo_{i}', '').strip()
        bruto = post.get(f'monto_{i}', '').strip()
        referencia = post.get(f'ref_{i}', '').strip()
        if not (metodo_id or bruto or referencia):
            continue  # línea vacía
        if not metodo_id or not bruto:
            raise CobroNoPermitido(
                f'Línea {i}: elige el método y escribe el monto.')
        metodo = None
        if metodo_id.isdigit():
            metodo = MetodoPago.objects.filter(pk=metodo_id, activo=True).first()
        if metodo is None:
            raise CobroNoPermitido(f'Línea {i}: método de pago no válido.')
        monto = _parse_monto(bruto)
        if monto is None:
            raise CobroNoPermitido(
                f'Línea {i}: el monto debe ser un número entero de pesos.')
        if len(referencia) > 60:
            raise CobroNoPermitido(
                f'Línea {i}: la referencia no puede pasar de 60 caracteres.')
        if metodo.pide_referencia and not referencia:
            raise CobroNoPermitido(
                f'Línea {i}: {metodo.nombre} requiere anotar la referencia.')
        lineas.append((metodo, monto, referencia))
    return lineas


@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def lista(request):
    es_admin = request.user.rol.codigo == Rol.ADMIN
    base = Cuenta.objects.select_related('cliente')
    abiertas = [
        c for c in base.filter(estado=Cuenta.Estado.ABIERTA).order_by('creada')
        if c.total > 0]
    # La lista de pendientes (deudas) la ve solo el administrador.
    pendientes = (list(base.filter(estado=Cuenta.Estado.PENDIENTE)
                       .order_by('creada')) if es_admin else [])
    return render(request, 'cuentas/lista.html', {
        'abiertas': abiertas, 'pendientes': pendientes, 'es_admin': es_admin})


@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def detalle(request, pk):
    cuenta = get_object_or_404(Cuenta.objects.select_related('cliente'), pk=pk)
    pedidos = (cuenta.pedidos.exclude(estado=Pedido.Estado.CANCELADO)
               .prefetch_related('detalles').order_by('creado'))
    otras_pendientes = []
    if cuenta.estado == Cuenta.Estado.ABIERTA:
        otras_pendientes = list(Cuenta.objects.filter(
            cliente=cuenta.cliente, estado=Cuenta.Estado.PENDIENTE))
    return render(request, 'cuentas/detalle.html', {
        'cuenta': cuenta,
        'pedidos': pedidos,
        'otras_pendientes': otras_pendientes,
        'metodos': MetodoPago.objects.filter(activo=True),
        'lineas': range(1, LINEAS + 1),
        'puede_cobrar': cuenta.estado in (
            Cuenta.Estado.ABIERTA, Cuenta.Estado.PENDIENTE),
        'es_admin': request.user.rol.codigo == Rol.ADMIN,
    })


@require_POST
@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def cobrar(request, pk):
    es_admin = request.user.rol.codigo == Rol.ADMIN
    try:
        lineas = _leer_lineas(request.POST)
        cuenta = cobrar_cuenta(pk, lineas, request.user, es_admin)
    except CobroNoPermitido as error:
        messages.error(request, str(error))
        return redirect('cuenta_detalle', pk=pk)
    if cuenta.estado == Cuenta.Estado.PAGADA:
        messages.success(
            request, f'Cuenta pagada. Comprobante No. {cuenta.numero}.')
    else:
        messages.warning(
            request, f'Pago registrado. Queda un saldo pendiente de '
                     f'${cuenta.saldo:,.0f}.')
    return redirect('cuenta_detalle', pk=pk)


@require_POST
@rol_requerido(Rol.ADMIN)
def pendiente(request, pk):
    try:
        dejar_pendiente(pk, request.user)
        messages.warning(request, 'La cuenta quedó pendiente de pago.')
    except CobroNoPermitido as error:
        messages.error(request, str(error))
    return redirect('cuenta_detalle', pk=pk)

@login_required
def comprobante(request, pk):
    cuenta = get_object_or_404(
        Cuenta.objects.select_related('cliente'),
        pk=pk, estado=Cuenta.Estado.PAGADA)
    codigo = request.user.rol.codigo if request.user.rol else None
    es_personal = codigo in (Rol.ADMIN, Rol.SERVICIO)
    if cuenta.cliente_id != request.user.id and not es_personal:
        raise Http404  # 404 y no 403: no revela que esa cuenta existe
    pagos = list(cuenta.pagos.select_related('metodo'))
    pedidos = (cuenta.pedidos.exclude(estado=Pedido.Estado.CANCELADO)
               .prefetch_related('detalles').order_by('creado'))
    return render(request, 'cuentas/comprobante.html', {
        'cuenta': cuenta,
        'pedidos': pedidos,
        'pagos': pagos,
        'fecha_pago': pagos[-1].creado if pagos else cuenta.cerrada,
    })
