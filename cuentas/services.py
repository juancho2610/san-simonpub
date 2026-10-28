#Configuracion del servicio para ejecutar las cuentas de los clientes
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from pedidos.models import Pedido
from usuarios.models import Usuario

from .models import Cuenta, Pago, Secuencia

EN_CURSO = [
    Pedido.Estado.RECIBIDO, Pedido.Estado.EN_PREPARACION,
    Pedido.Estado.LISTO, Pedido.Estado.EN_CAMINO,
]

#Clase de cobro no permitido
class CobroNoPermitido(Exception):
    """Mensaje pensado para mostrarse tal cual al personal."""


def cuenta_abierta_para(usuario):
    """Devuelve la cuenta ABIERTA del cliente, o crea una nueva.

    Debe llamarse DENTRO de transaction.atomic(). Bloquea la fila del
    cliente para que dos pedidos simultáneos no creen dos cuentas.
    Una cuenta PENDIENTE no cuenta: el pedido nuevo abre otra cuenta.
    """
    Usuario.objects.select_for_update().get(pk=usuario.pk)
    cuenta = Cuenta.objects.filter(
        cliente=usuario, estado=Cuenta.Estado.ABIERTA).first()
    if cuenta is None:
        cuenta = Cuenta.objects.create(cliente=usuario)
    return cuenta


def _congelar(cuenta, usuario):
    """Fija el total de la cuenta. Llamar dentro de transaction.atomic()."""
    sin_entregar = cuenta.pedidos.filter(estado__in=EN_CURSO).count()
    if sin_entregar:
        raise CobroNoPermitido(
            f'La cuenta tiene {sin_entregar} pedido(s) sin entregar. '
            'Márcalos como entregados en el tablero de pedidos.')
    total = cuenta.total
    if total <= 0:
        raise CobroNoPermitido('Esta cuenta no tiene nada que cobrar.')
    cuenta.total_cobrado = total
    cuenta.cobrada_por = usuario
    cuenta.cerrada = timezone.now()


def _siguiente_numero():
    secuencia = Secuencia.objects.select_for_update().get(nombre='comprobante')
    secuencia.ultimo += 1
    secuencia.save(update_fields=['ultimo'])
    return secuencia.ultimo


def cobrar_cuenta(cuenta_id, lineas, usuario, es_admin):
    """lineas: lista de (MetodoPago, monto Decimal, referencia)."""
    if not lineas:
        raise CobroNoPermitido('Registra al menos un pago.')
    with transaction.atomic():
        cuenta = Cuenta.objects.select_for_update().filter(pk=cuenta_id).first()
        if cuenta is None:
            raise CobroNoPermitido('Esa cuenta no existe.')
        if cuenta.estado not in (Cuenta.Estado.ABIERTA, Cuenta.Estado.PENDIENTE):
            raise CobroNoPermitido('Esta cuenta ya está cerrada.')
        if cuenta.total_cobrado is None:
            _congelar(cuenta, usuario)

        saldo = cuenta.total - cuenta.pagado
        suma = sum((monto for _, monto, _ in lineas), Decimal('0'))
        if suma > saldo:
            raise CobroNoPermitido(
                f'Los pagos suman más que el saldo (${saldo:,.0f}). '
                'Anota solo lo que se cobra.')
        if suma < saldo and not es_admin:
            raise CobroNoPermitido(
                f'El pago no cubre el saldo (${saldo:,.0f}). Si el cliente '
                'deja un saldo pendiente, debe autorizarlo el administrador.')

        for metodo, monto, referencia in lineas:
            Pago.objects.create(
                cuenta=cuenta, metodo=metodo, monto=monto,
                referencia=referencia, registrado_por=usuario)

        if suma == saldo:
            cuenta.estado = Cuenta.Estado.PAGADA
            cuenta.numero = _siguiente_numero()
        else:
            cuenta.estado = Cuenta.Estado.PENDIENTE
        cuenta.save()
        return cuenta


def dejar_pendiente(cuenta_id, usuario):
    with transaction.atomic():
        cuenta = Cuenta.objects.select_for_update().filter(pk=cuenta_id).first()
        if cuenta is None:
            raise CobroNoPermitido('Esa cuenta no existe.')
        if cuenta.estado != Cuenta.Estado.ABIERTA:
            raise CobroNoPermitido('Solo una cuenta abierta se puede dejar pendiente.')
        _congelar(cuenta, usuario)
        cuenta.estado = Cuenta.Estado.PENDIENTE
        cuenta.save()
        return cuenta


def anular_cuenta(cuenta_id, usuario, motivo):
    motivo = (motivo or '').strip()
    if len(motivo) < 10:
        raise CobroNoPermitido(
            'Escribe el motivo de la anulación (mínimo 10 caracteres).')
    if len(motivo) > 200:
        raise CobroNoPermitido(
            'El motivo no puede pasar de 200 caracteres.')
    with transaction.atomic():
        cuenta = Cuenta.objects.select_for_update().filter(pk=cuenta_id).first()
        if cuenta is None:
            raise CobroNoPermitido('Esa cuenta no existe.')
        if cuenta.estado not in (Cuenta.Estado.PAGADA, Cuenta.Estado.PENDIENTE):
            raise CobroNoPermitido(
                'Solo se puede anular una cuenta pagada o pendiente.')
        cuenta.estado = Cuenta.Estado.ANULADA
        cuenta.motivo_anulacion = motivo
        cuenta.anulada_por = usuario
        cuenta.anulada = timezone.now()
        cuenta.save(update_fields=[
            'estado', 'motivo_anulacion', 'anulada_por', 'anulada'])
        return cuenta

