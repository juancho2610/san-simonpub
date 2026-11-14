from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Rol
from usuarios.views import rol_requerido

from .models import Cancion, SolicitudMusical
from .services import (ACTIVAS, SolicitudNoPermitida, avanzar_cola,
                       pedido_habilitante, solicitar_cancion)


def _es_fetch(request):
    return request.headers.get('X-Requested-With') == 'fetch'


def _estado(usuario):
    """Lo que ve un cliente: qué suena, qué sigue y qué puede pedir.
    Nunca incluye el nombre de quien pidió cada canción."""
    activas = list(
        SolicitudMusical.objects.filter(estado__in=ACTIVAS)
        .select_related('cancion').order_by('creada'))
    sonando = next((s for s in activas
                    if s.estado == SolicitudMusical.Estado.REPRODUCIENDO), None)
    pendientes = [s for s in activas
                  if s.estado == SolicitudMusical.Estado.EN_COLA]
    return {
        'sonando': None if sonando is None else {
            'titulo': sonando.cancion.titulo,
            'artista': sonando.cancion.artista,
            'mia': sonando.cliente_id == usuario.id,
        },
        'cola': [{
            'id': s.pk,
            'titulo': s.cancion.titulo,
            'artista': s.cancion.artista,
            'mia': s.cliente_id == usuario.id,
        } for s in pendientes],
        'en_cola_ids': [s.cancion_id for s in activas],
        'mis_activas': sum(1 for s in activas if s.cliente_id == usuario.id),
        'maximo': settings.MUSICA_MAX_EN_COLA_POR_CLIENTE,
        'puede_pedir': pedido_habilitante(usuario) is not None,
        'horas': settings.MUSICA_VENTANA_PEDIDO_HORAS,
    }


@rol_requerido(Rol.CLIENTE)
def catalogo(request):
    q = request.GET.get('q', '').strip()
    canciones = Cancion.objects.filter(activa=True)
    if q:
        canciones = canciones.filter(
            Q(titulo__icontains=q) | Q(artista__icontains=q))
    pagina = Paginator(canciones, 20).get_page(request.GET.get('page'))
    return render(request, 'musica/catalogo.html', {
        'pagina': pagina, 'q': q, 'estado': _estado(request.user)})


@require_GET
@rol_requerido(Rol.CLIENTE)
def estado(request):
    return JsonResponse(_estado(request.user))


@require_POST
@rol_requerido(Rol.CLIENTE)
def pedir(request, pk):
    try:
        solicitud = solicitar_cancion(request.user, pk)
        texto, ok = f'"{solicitud.cancion.titulo}" quedó en la cola.', True
    except SolicitudNoPermitida as error:
        texto, ok = str(error), False
    if _es_fetch(request):
        return JsonResponse({'ok': ok, 'mensaje': texto})
    (messages.success if ok else messages.error)(request, texto)
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
            texto, ok = 'Cancelaste tu canción.', True
        else:
            texto, ok = 'Esa canción ya no se puede cancelar.', False
    if _es_fetch(request):
        return JsonResponse({'ok': ok, 'mensaje': texto})
    (messages.success if ok else messages.error)(request, texto)
    return redirect('catalogo_musical')


def _respuesta_cola(solicitud):
    proximas = (
        SolicitudMusical.objects
        .filter(estado=SolicitudMusical.Estado.EN_COLA)
        .select_related('cancion').order_by('creada')[:8])
    sonando = None
    if solicitud is not None:
        c = solicitud.cancion
        sonando = {'id': solicitud.pk, 'titulo': c.titulo,
                   'artista': c.artista, 'url': c.archivo.url}
    return JsonResponse({
        'sonando': sonando,
        'proximas': [f'{s.cancion.titulo} — {s.cancion.artista}'
                     for s in proximas],
    })


def _id_enviado(request, campo):
    try:
        return int(request.POST.get(campo, ''))
    except ValueError:
        return None


@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def reproductor(request):
    return render(request, 'musica/reproductor.html')


@require_GET
@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def api_estado(request):
    """Solo consulta: nunca cambia la cola ni arranca canciones."""
    actual = (SolicitudMusical.objects
              .filter(estado=SolicitudMusical.Estado.REPRODUCIENDO)
              .select_related('cancion').first())
    return _respuesta_cola(actual)


@require_POST
@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def api_siguiente(request):
    solicitud = avanzar_cola(_id_enviado(request, 'terminada'))
    return _respuesta_cola(solicitud)


@require_POST
@rol_requerido(Rol.ADMIN, Rol.SERVICIO)
def api_omitir(request):
    solicitud = avanzar_cola(
        _id_enviado(request, 'id'), SolicitudMusical.Estado.OMITIDA)
    return _respuesta_cola(solicitud)
