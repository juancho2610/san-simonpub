#Configurar aplicaciones
from django.apps import AppConfig


#Clase de configurar Usuarios
class UsuariosConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'usuarios'

