from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Usuario del sistema. Extiende el usuario base de Django añadiendo
    el rol, que determina qué puede ver y hacer cada persona en el portal.

    Roles actuales (fase núcleo):
    - administrador: acceso total al sistema.
    - tecnico: acceso a inventario y operación de campo, sin acceso
      a configuración global ni gestión de usuarios.
    - comercial: acceso a inventario y gfestión de susuarios
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        TECNICO = 'tecnico', 'Técnico de campo'
        COMERCIAL = 'comercial', 'Comercial'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.TECNICO,
        verbose_name='Rol',
    )
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    activo_en_campo = models.BooleanField(
        default=True,
        verbose_name='Disponible para asignación de tareas',
        help_text='Solo aplica a técnicos; permite marcarlos como no disponibles temporalmente.',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_tecnico(self):
        return self.rol == self.Rol.TECNICO
        
    @property
    def es_comercial(self):
        return self.rol == self.Rol.COMERCIAL

