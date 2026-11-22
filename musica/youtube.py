"""Búsqueda de canciones en YouTube (API Data v3), con caché y tope de cupo.
Solo se llama desde el servidor: la clave nunca llega al navegador."""
import html
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from .models import BusquedaYoutube

logger = logging.getLogger(__name__)

URL_BUSQUEDA = 'https://www.googleapis.com/youtube/v3/search'
COSTO_BUSQUEDA = 100          # unidades de cupo que cobra search.list
PACIFICO = ZoneInfo('America/Los_Angeles')   # el cupo se reinicia a su medianoche
CATEGORIA_MUSICA = '10'


class YoutubeNoDisponible(Exception):
    """Mensaje pensado para mostrarse tal cual al cliente."""


def _normalizar(consulta):
    return ' '.join((consulta or '').lower().split())[:100]


def _inicio_dia_pacifico():
    ahora = timezone.now().astimezone(PACIFICO)
    return ahora.replace(hour=0, minute=0, second=0, microsecond=0)


def busquedas_hoy():
    return BusquedaYoutube.objects.filter(creada__gte=_inicio_dia_pacifico())


def cupo_gastado_hoy():
    return busquedas_hoy().count() * COSTO_BUSQUEDA


def _limpiar(item):
    video_id = (item.get('id') or {}).get('videoId', '')
    if not re.fullmatch(r'[\w-]{11}', video_id):
        return None
    snippet = item.get('snippet') or {}
    return {
        'id': video_id,
        # YouTube devuelve los textos con entidades HTML (&amp;, &#39;...)
        'titulo': html.unescape(snippet.get('title', ''))[:120],
        'canal': html.unescape(snippet.get('channelTitle', ''))[:120],
    }


def _consultar_youtube(consulta):
    parametros = urllib.parse.urlencode({
        'part': 'snippet', 'type': 'video', 'maxResults': 8, 'q': consulta,
        'videoCategoryId': CATEGORIA_MUSICA,
        'videoEmbeddable': 'true', 'videoSyndicated': 'true',
        'regionCode': 'CO',
    })
    peticion = urllib.request.Request(
        f'{URL_BUSQUEDA}?{parametros}',
        headers={'x-goog-api-key': settings.YOUTUBE_API_KEY})
    try:
        with urllib.request.urlopen(peticion, timeout=8) as r:
            datos = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            motivo = json.load(e)['error']['errors'][0]['reason']
        except Exception:
            motivo = 'desconocido'
        logger.warning('YouTube respondió %s (%s)', e.code, motivo)
        if motivo in ('quotaExceeded', 'dailyLimitExceeded', 'rateLimitExceeded'):
            raise YoutubeNoDisponible(
                'Se agotaron las búsquedas de hoy. Vuelve a intentarlo más tarde.')
        raise YoutubeNoDisponible(
            'No pudimos buscar música en este momento. Intenta de nuevo.')
    except Exception as e:
        logger.warning('Fallo de red con YouTube: %s', type(e).__name__)
        raise YoutubeNoDisponible(
            'No pudimos buscar música en este momento. Intenta de nuevo.')
    resultados = [_limpiar(i) for i in datos.get('items', [])]
    return [r for r in resultados if r]


def buscar(consulta, usuario=None):
    """Devuelve una lista de {'id', 'titulo', 'canal'}. Orden de las reglas:
    caché -> tope por cliente -> tope global -> pregunta a YouTube."""
    q = _normalizar(consulta)
    if len(q) < 2:
        raise YoutubeNoDisponible('Escribe al menos 2 letras para buscar.')
    if not settings.YOUTUBE_API_KEY:
        raise YoutubeNoDisponible('La búsqueda de música no está disponible por ahora.')

    reciente = timezone.now() - timedelta(hours=settings.YOUTUBE_CACHE_HORAS)
    guardada = BusquedaYoutube.objects.filter(
        consulta=q, creada__gte=reciente).first()
    if guardada:
        return guardada.resultados

    hoy = busquedas_hoy()
    if usuario is not None and hoy.filter(usuario=usuario).count() \
            >= settings.YOUTUBE_BUSQUEDAS_MAX_POR_CLIENTE:
        raise YoutubeNoDisponible(
            'Ya hiciste varias búsquedas nuevas hoy. Prueba con las canciones '
            'del catálogo o con búsquedas que otros ya hicieron.')
    if hoy.count() >= settings.YOUTUBE_BUSQUEDAS_MAX_DIA:
        raise YoutubeNoDisponible(
            'Se agotaron las búsquedas de hoy. Puedes pedir canciones del catálogo.')

    resultados = _consultar_youtube(q)
    BusquedaYoutube.objects.create(
        consulta=q, resultados=resultados, usuario=usuario)
    return resultados


def purgar_busquedas(dias=7):
    """Borra búsquedas viejas (la política de la API pide no guardar datos
    por más de 30 días). Devuelve cuántas borró."""
    limite = timezone.now() - timedelta(days=dias)
    return BusquedaYoutube.objects.filter(creada__lt=limite).delete()[0]
