#Servicios de reproduccion y cola de canciones
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from pedidos.models import Pedido
from usuarios.models import Usuario

from .models import Cancion, SolicitudMusical

ACTIVAS = [SolicitudMusical.Estado.EN_COLA,
           SolicitudMusical.Estado.REPRODUCIENDO]


class SolicitudNoPermitida(Exception):
    """Mensaje pensado para mostrarse tal cual al cliente."""


def pedido_habilitante(usuario):
    """Pedido EN MESA, no cancelado, dentro de la ventana de horas asignadas 8 horas maximo."""
    desde = timezone.now() - timedelta(
        hours=settings.MUSICA_VENTANA_PEDIDO_HORAS)
    return (
        Pedido.objects
        .filter(cliente=usuario, tipo=Pedido.Tipo.EN_MESA, creado__gte=desde)
        .exclude(estado=Pedido.Estado.CANCELADO)
        .order_by('-creado')
        .first()
    )


def solicitudes_activas(usuario):
    return SolicitudMusical.objects.filter(
        cliente=usuario, estado__in=ACTIVAS).count()


def solicitar_cancion(usuario, cancion_id):
    maximo = settings.MUSICA_MAX_EN_COLA_POR_CLIENTE
    with transaction.atomic():
        # Primero los bloqueos, después las comprobaciones.
        Usuario.objects.select_for_update().get(pk=usuario.pk)
        cancion = (Cancion.objects.select_for_update()
                   .filter(pk=cancion_id, activa=True).first())
        if cancion is None:
            raise SolicitudNoPermitida('Esa canción no está disponible.')

        pedido = pedido_habilitante(usuario)
        if pedido is None:
            raise SolicitudNoPermitida(
                'Para pedir canciones necesitas un pedido en mesa de las '
                f'últimas {settings.MUSICA_VENTANA_PEDIDO_HORAS} horas.')

        if solicitudes_activas(usuario) >= maximo:
            raise SolicitudNoPermitida(
                f'Ya tienes {maximo} canciones en la cola. '
                'Espera a que suene alguna.')

        if SolicitudMusical.objects.filter(
                cancion=cancion, estado__in=ACTIVAS).exists():
            raise SolicitudNoPermitida(
                'Esa canción ya está en la cola. Elige otra o espera '
                'a que suene.')

        return SolicitudMusical.objects.create(
            cancion=cancion, cliente=usuario, pedido=pedido)
