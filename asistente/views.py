from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import respaldo
from .models import Interaccion


@login_required
def chat(request):
    return render(request, 'asistente/chat.html',
                  {'temas': respaldo.TEMAS.items()})


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
