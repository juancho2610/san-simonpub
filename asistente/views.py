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
        'temas': respaldo.TEMAS.items(),
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
        respuesta, uso_ia, restantes = servicio.preguntar(
            request.user, texto, historial)
    except servicio.LimiteAlcanzado as limite:
        if str(limite) == 'global':
            aviso = ('El asistente está muy ocupado hoy. Usa los botones de '
                     'temas o pregunta al personal.')
        else:
            aviso = ('Llegaste al límite de mensajes de hoy. Puedes seguir con '
                     'los botones de temas o preguntar al personal.')
        return JsonResponse({'error': aviso}, status=429)

    if uso_ia:  # solo se recuerda lo que la IA respondió
        historial += [{'role': 'user', 'content': texto},
                      {'role': 'assistant', 'content': respuesta}]
        request.session[CLAVE_HISTORIAL] = historial[-settings.ASISTENTE_HISTORIAL:]
    return JsonResponse({'texto': respuesta, 'ia': uso_ia, 'restantes': restantes})
