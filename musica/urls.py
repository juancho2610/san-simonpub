from django.urls import path

from . import views

urlpatterns = [
    path('musica/', views.catalogo, name='catalogo_musical'),
    path('musica/estado/', views.estado, name='estado_musica'),
    path('musica/pedir/<int:pk>/', views.pedir, name='pedir_cancion'),
    path('musica/cancelar/<int:pk>/', views.cancelar, name='cancelar_cancion'),
    path('musica/youtube/buscar/', views.buscar_youtube, name='buscar_youtube'),
    path('musica/youtube/pedir/', views.pedir_youtube, name='pedir_youtube'),
    path('personal/musica/', views.reproductor, name='reproductor'),
    path('personal/musica/estado/', views.api_estado, name='api_estado'),
    path('personal/musica/siguiente/', views.api_siguiente, name='api_siguiente'),
    path('personal/musica/omitir/', views.api_omitir, name='api_omitir'),
]
