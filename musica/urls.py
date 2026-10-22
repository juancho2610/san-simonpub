#Direcciones de servicios de musica
from django.urls import path

from . import views

urlpatterns = [
    path('musica/', views.catalogo, name='catalogo_musical'),
    path('musica/pedir/<int:pk>/', views.pedir, name='pedir_cancion'),
    path('musica/cancelar/<int:pk>/', views.cancelar, name='cancelar_cancion'),
    path('personal/musica/', views.reproductor, name='reproductor'),
    path('personal/musica/siguiente/', views.api_siguiente, name='api_siguiente'),
    path('personal/musica/omitir/', views.api_omitir, name='api_omitir'),
]
