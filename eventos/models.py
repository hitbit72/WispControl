from django.conf import settings
from django.db import models


class Evento(models.Model):
    """
    Evento registrado durante la ejecución de la aplicación. No se crean a
    mano: los módulos usan la función común `eventos.services.registrar_evento`
    para avisar aquí de lo importante o de los errores.
    """

    class Nivel(models.IntegerChoices):
        EMERG = 0, 'Emerg'
        ALERT = 1, 'Alert'
        CRITICAL = 2, 'Critical'
        ERROR = 3, 'Error'
        WARNING = 4, 'Warning'
        NOTICE = 5, 'Notice'
        INFO = 6, 'Info'

    # Clase de badge Bootstrap por nivel (para las plantillas).
    NIVEL_BADGE = {
        Nivel.EMERG: 'danger',
        Nivel.ALERT: 'danger',
        Nivel.CRITICAL: 'danger',
        Nivel.ERROR: 'danger',
        Nivel.WARNING: 'warning text-dark',
        Nivel.NOTICE: 'info text-dark',
        Nivel.INFO: 'secondary',
    }

    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')
    nivel = models.PositiveSmallIntegerField(
        choices=Nivel.choices, default=Nivel.INFO, verbose_name='Nivel',
    )
    titulo = models.CharField(max_length=255, verbose_name='Título')
    texto = models.TextField(blank=True, verbose_name='Texto')
    modulo = models.CharField(max_length=100, blank=True, verbose_name='Módulo')
    leido = models.BooleanField(default=False, verbose_name='Leído')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='eventos_leidos',
        verbose_name='Marcado como leído por',
    )

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        # Orden primero por fecha descendente y
        # después por nivel (0 = el más importante)
        ordering = ['-fecha', 'nivel']

    def __str__(self):
        return f'[{self.get_nivel_display()}] {self.titulo} ({self.modulo})'

    @property
    def color_badge(self):
        return self.NIVEL_BADGE.get(self.nivel, 'secondary')
