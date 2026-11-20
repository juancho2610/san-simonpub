#Modelo para administar el menu
from django.contrib import admin

from .models import Categoria, GrupoOpciones, Opcion, Producto
# administrar el menu
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activa')
    list_editable = ('orden', 'activa')

#Clase Grupo de opciones
class GrupoInline(admin.TabularInline):
    model = GrupoOpciones
    extra = 0
    fields = ('nombre', 'obligatorio', 'max_selecciones', 'orden')
    show_change_link = True  # enlace para entrar al grupo y carga opciones

#Clase producto segun la categoria
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio','precio_desde', 'disponible')
    list_editable = ('precio', 'precio_desde', 'disponible')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre', 'descripcion')
    inlines = [GrupoInline]


#Clase de  de opciones del administrador
class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 3
    fields = ('nombre', 'precio_extra', 'disponible', 'orden')


#Grupo de opciones por lista
@admin.register(GrupoOpciones)
class GrupoOpcionesAdmin(admin.ModelAdmin):
    list_display = ('producto', 'nombre', 'obligatorio', 'max_selecciones')
    list_filter = ('producto__categoria',)
    search_fields = ('producto__nombre', 'nombre')
    inlines = [OpcionInline]
