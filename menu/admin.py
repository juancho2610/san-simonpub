#Modelo para administar el menu
from django.contrib import admin

from .models import Categoria, Producto
# Register your models here.
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activa')
    list_editable = ('orden', 'activa')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'disponible')
    list_editable = ('precio', 'disponible')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre', 'descripcion')
