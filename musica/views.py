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
                       pedido_habilitante, solicitar_cancion,
                       solicitar_desde_youtube)
from .youtube import YoutubeNoDisponible, buscar


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
        'en_cola_youtube': [s.cancion.youtube_id for s in activas
                            if s.cancion.youtube_id],
        'mis_activas': sum(1 for s in activas if s.cliente_id == usuario.id),
        'maximo': settings.MUSICA_MAX_EN_COLA_POR_CLIENTE,
        'puede_pedir': pedido_habilitante(usuario) is not None,
        'horas': settings.MUSICA_VENTANA_PEDIDO_HORAS,
    }


@rol_requerido(Rol.CLIENTE)
def catalogo(request):
    q = request.GET.get('q', '').strip()
    canciones = Cancion.objects.filter(activa=True).exclude(archivo='')
    if q:
        canciones = canciones.filter(
            Q(titulo__icontains=q) | Q(artista__icontains=q))
    pagina = Paginator(canciones, 20).get_page(request.GET.get('page'))
    return render(request, 'musica/catalogo.html', {
        'pagina': pagina, 'q': q, 'estado': _estado(request.user),
        'archivos_activo': settings.MUSICA_ARCHIVOS_ACTIVO})


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
                   'artista': c.artista,
                   'url': c.archivo.url if c.archivo else None,
                   'youtube_id': c.youtube_id}
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
    omitida = _id_enviado(request, 'id')
    if request.POST.get('no_disponible') == '1' and omitida is not None:
        # El video falló en el reproductor: no se vuelve a ofrecer.
        for c in Cancion.objects.filter(
                solicitudes__pk=omitida, youtube_id__isnull=False):
            c.activa = False
            c.save(update_fields=['activa'])
    solicitud = avanzar_cola(omitida, SolicitudMusical.Estado.OMITIDA)
    return _respuesta_cola(solicitud)


@require_GET
@rol_requerido(Rol.CLIENTE)
def buscar_youtube(request):
    # Buscar gasta cupo del bar: solo quien puede pedir puede buscar.
    if pedido_habilitante(request.user) is None:
        return JsonResponse({'ok': False, 'mensaje':
            'Para buscar canciones necesitas un pedido en mesa de las '
            f'últimas {settings.MUSICA_VENTANA_PEDIDO_HORAS} horas.'})
    try:
        resultados = buscar(request.GET.get('q', ''), request.user)
    except YoutubeNoDisponible as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)})
    bloqueadas = set(Cancion.objects.filter(
        youtube_id__in=[r['id'] for r in resultados], activa=False
    ).values_list('youtube_id', flat=True))
    resultados = [r for r in resultados if r['id'] not in bloqueadas]
    return JsonResponse({'ok': True, 'resultados': resultados})


@require_POST
@rol_requerido(Rol.CLIENTE)
def pedir_youtube(request):
    try:
        solicitud = solicitar_desde_youtube(
            request.user, request.POST.get('video_id', ''))
        texto, ok = f'"{solicitud.cancion.titulo}" quedó en la cola.', True
    except SolicitudNoPermitida as error:
        texto, ok = str(error), False
    return JsonResponse({'ok': ok, 'mensaje': texto})
