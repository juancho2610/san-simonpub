#Modelo de url para la IA
from django.urls import path

from . import views

urlpatterns = [
    path('asistente/', views.chat, name='asistente'),
    path('asistente/tema/', views.tema, name='asistente_tema'),
    path('asistente/mensaje/', views.mensaje, name='asistente_mensaje'),
]
