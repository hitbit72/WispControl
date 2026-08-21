from django.db import models

# Base de datos core, población, Tipo de documento. Accesible desde administracion


class Provincia(models.Model):
    """Provincias de Cliente (persona o empresa)"""
    nombre = models.CharField(max_length=255, verbose_name='Provincia')

    class Meta:
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre}'
    
class Poblacion(models.Model):
    """Poblaciones de Cliente (persona o empresa)"""
    nombre = models.CharField(max_length=255, verbose_name='Población')
    provincia = models.ForeignKey(Provincia,null=True, blank=True, on_delete=models.SET_NULL, related_name='poblaciones')

    class Meta:
        verbose_name = 'Población'
        verbose_name_plural = 'Poblaciones'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre}'

