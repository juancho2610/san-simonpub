#Configuracion de las vistas de musica en general
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Rol
from usuarios.views import rol_requerido

from .models import Cancion, SolicitudMusical
from .services import (ACTIVAS, SolicitudNoPermitida, pedido_habilitante, solicitar_cancion, solicitudes_activas)

# Clase de catalogo de musica.
# Acceso permito segun el rol asignado
@rol_requerido(Rol.CLIENTE)
def catalogo(request):
    q = request.GET.get('q', '').strip()
    canciones = Cancion.objects.filter(activa=True)
    if q:
        canciones = canciones.filter(
            Q(titulo__icontains=q) | Q(artista__icontains=q))
    pagina = Paginator(canciones, 20).get_page(request.GET.get('page'))

    cola = (SolicitudMusical.objects.filter(estado__in=ACTIVAS)
            .select_related('cancion').order_by('creada'))
    contexto = {
        'pagina': pagina,
        'q': q,
        'cola': cola,
        'en_cola_ids': {s.cancion_id for s in cola},
        'puede_pedir': pedido_habilitante(request.user) is not None,
        'mis_activas': solicitudes_activas(request.user),
        'maximo': settings.MUSICA_MAX_EN_COLA_POR_CLIENTE,
        'horas': settings.MUSICA_VENTANA_PEDIDO_HORAS,
    }
    return render(request, 'musica/catalogo.html', contexto)


@require_POST
@rol_requerido(Rol.CLIENTE)
def pedir(request, pk):
    try:
        solicitud = solicitar_cancion(request.user, pk)
        messages.success(
            request, f'"{solicitud.cancion.titulo}" quedó en la cola.')
    except SolicitudNoPermitida as error:
        messages.error(request, str(error))
    return redirect('catalogo_musical')


@require_POST
@rol_requerido(Rol.CLIENTE)
def cancelar(request, pk):
    with transaction.atomic():
        solicitud = get_object_or_404(
            SolicitudMusical.objects.select_for_update(),
            pk=pk, cliente=request.user)
        if solicitud.estado == SolicitudMusical.Estado.EN_COLA:
            solicitud.estado = SolicitudMusical.Estado.CANCELADA
            solicitud.save(update_fields=['estado'])
            messages.success(request, 'Cancelaste tu canción.')
        else:
            messages.error(request, 'Esa canción ya no se puede cancelar.')
    return redirect('catalogo_musical')
