from usuarios.models import Usuario

from .models import Cuenta


def cuenta_abierta_para(usuario):
    """Devuelve la cuenta vigente del cliente, o crea una nueva.

    Debe llamarse DENTRO de transaction.atomic(). Bloquea la fila del
    cliente para que dos pedidos simultáneos no creen dos cuentas.
    """
    Usuario.objects.select_for_update().get(pk=usuario.pk)
    cuenta = Cuenta.objects.filter(
        cliente=usuario, estado__in=Cuenta.VIGENTES).first()
    if cuenta is None:
        return Cuenta.objects.create(cliente=usuario)
    # Si ya había pedido el cobro y agrega algo más, vuelve a "abierta"
    # para que el personal no cobre una cuenta incompleta.
    if cuenta.estado == Cuenta.Estado.SOLICITADA:
        cuenta.estado = Cuenta.Estado.ABIERTA
        cuenta.save(update_fields=['estado'])
    return cuenta
