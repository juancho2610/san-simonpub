#Configuracion del administrador
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Rol, Usuario

@admin.register(Rol)
#Clase Rol del Administrador
class RolAdmin(admin.ModelAdmin):
	list_display = ('nombre','codigo')


@admin.register(Usuario)
#Usuario Administrador
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('San Simón Pub', {'fields': ('rol', 'telefono')}),
    )
    list_display = ('username', 'email', 'rol', 'is_active')
    list_filter = ('rol', 'is_active')

