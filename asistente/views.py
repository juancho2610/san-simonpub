#Modelo de la vista de la IA
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from usuarios.models import Rol
from usuarios.views import rol_requerido

from . import respaldo, servicio
from .models import Interaccion

CLAVE_HISTORIAL = 'asistente_historial'


def _leer_historial(request):
    """Historial de la sesión, validado: nunca se confía en su forma."""
    bruto = request.session.get(CLAVE_HISTORIAL, [])
    limpio = []
    if isinstance(bruto, list):
        for item in bruto:
            if (isinstance(item, dict)
                    and item.get('role') in ('user', 'assistant')
                    and isinstance(item.get('content'), str)):
                limpio.append({'role': item['role'], 'content': item['content'][:2000]})
    limpio = limpio[-settings.ASISTENTE_HISTORIAL:]
    while limpio and limpio[0]['role'] != 'user':
        limpio.pop(0)
    return limpio


@login_required
def chat(request):
    usados = servicio.usados_hoy(request.user)
    return render(request, 'asistente/chat.html', {
        'max_caracteres': settings.ASISTENTE_MAX_CARACTERES,
        'restantes': max(0, settings.ASISTENTE_MAX_MENSAJES_DIA - usados),
        'dias': settings.ASISTENTE_RETENCION_DIAS,
    })


@require_POST
@login_required
def tema(request):
    clave = request.POST.get('tema', '')
    respuesta = respaldo.responder(clave)
    if respuesta is None:
        return JsonResponse({'error': 'Tema no válido.'}, status=400)
    Interaccion.objects.create(
        usuario=request.user, tema=clave, respuesta=respuesta['texto'],
        origen=Interaccion.Origen.RESPALDO)
    return JsonResponse(respuesta)


def _respuesta_fija(request, texto, nota, restantes):
    """Responde con información fija cuando la IA no puede. None si nada encaja."""
    alternativa = respaldo.responder_por_texto(texto)
    if alternativa is None:
        return None
    Interaccion.objects.create(
        usuario=request.user, tema=alternativa['tema'], pregunta=texto,
        respuesta=alternativa['texto'], origen=Interaccion.Origen.RESPALDO)
    return JsonResponse({
        'texto': f"{alternativa['texto']}\n\n({nota})",
        'ia': False, 'restantes': restantes, 'productos': [],
        'enlace': alternativa['enlace'],
    })


@require_POST
@rol_requerido(Rol.CLIENTE, Rol.ADMIN)
def mensaje(request):
    texto = request.POST.get('mensaje', '').strip()
    if not texto:
        return JsonResponse({'error': 'Escribe tu pregunta.'}, status=400)
    if len(texto) > settings.ASISTENTE_MAX_CARACTERES:
        return JsonResponse(
            {'error': f'Máximo {settings.ASISTENTE_MAX_CARACTERES} caracteres.'},
            status=400)

    historial = _leer_historial(request)
    try:
        respuesta, uso_ia, restantes, productos = servicio.preguntar(
            request.user, texto, historial)
    except servicio.LimiteAlcanzado as limite:
        if str(limite) == 'global':
            aviso = ('El asistente está muy ocupado hoy. Pregunta al personal '
                     'o vuelve a intentarlo más tarde.')
        else:
            aviso = ('Llegaste al límite de mensajes de hoy. Puedes preguntar '
                     'al personal o volver mañana.')
        quedan = max(0, settings.ASISTENTE_MAX_MENSAJES_DIA - servicio.usados_hoy(request.user))
        fija = _respuesta_fija(request, texto, aviso, quedan)
        return fija or JsonResponse({'error': aviso}, status=429)

    if not uso_ia:
        fija = _respuesta_fija(
            request, texto,
            'Ahora mismo no puedo usar la inteligencia artificial; '
            'esta es una respuesta automática.', restantes)
        if fija:
            return fija
    if uso_ia:  # solo se recuerda lo que la IA respondió
        historial += [{'role': 'user', 'content': texto},
                      {'role': 'assistant', 'content': respuesta}]
        request.session[CLAVE_HISTORIAL] = historial[-settings.ASISTENTE_HISTORIAL:]
    return JsonResponse({'texto': respuesta, 'ia': uso_ia, 'restantes': restantes, 'productos': productos})
