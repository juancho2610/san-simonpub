#Configurar Usuarios
from django.contrib.auth.models import AbstractUser
from django.db import models

#Clase rol para administrador,personal de cocina y bar,clientes y servicios.
class Rol(models.Model):
    ADMIN = 'ADMIN'
    SERVICIO = 'SERVICIO'
    COCINA_BAR = 'COCINA_BAR'
    CLIENTE = 'CLIENTE'

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'rol'
        verbose_name_plural = 'roles'

    def __str__(self):
        return self.nombre

#Clase Usuario
class Usuario(AbstractUser):
    email = models.EmailField('correo electrónico', unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, related_name='usuarios',
        null=True, blank=True,
    )

    def save(self, *args, **kwargs):
        # Un superusuario siempre es Administrador.
        # Si no hay rol, se asigna Cliente por seguridad (el rol con menos poder).
        if self.is_superuser:
            self.rol = Rol.objects.filter(codigo=Rol.ADMIN).first()
        elif self.rol_id is None:
            self.rol = Rol.objects.filter(codigo=Rol.CLIENTE).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.rol})'
