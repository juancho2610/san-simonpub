from django.contrib import admin

from .models import Cancion, SolicitudMusical

# Modelo a nivel de administracion para la musica
#Acceso solo  para la administracion
@admin.register(Cancion)
class CancionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'artista', 'activa')
    list_editable = ('activa',)
    search_fields = ('titulo', 'artista')


@admin.register(SolicitudMusical)
class SolicitudMusicalAdmin(admin.ModelAdmin):
    list_display = ('cancion', 'cliente', 'estado', 'creada')
    list_filter = ('estado',)
    readonly_fields = ('creada',)
