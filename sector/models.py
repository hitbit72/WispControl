from django.db import models


class Sector(models.Model):
    """
    Zona de cobertura o agrupación lógica de dispositivos (ej. 'Sector Norte',
    'Torre Centro'). Útil para organizar el inventario y, más adelante, el mapa.
    """
    nombre = models.CharField(max_length=100, unique=True)
    poblacion = models.ForeignKey('core.Poblacion', null=True, blank=True, on_delete=models.SET_NULL, related_name='sectores')
    direccion = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    altitud = models.IntegerField(default=0, null=True, blank=True, help_text='Altitud en metros sobre el nivel del mar.')

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} · ({self.poblacion.nombre})'

