from django import template
from django.utils.safestring import mark_safe  # <-- renderizar como HTML real

register = template.Library()


@register.filter
def cubre_frecuencia(dispositivo, freq_columna):
    """
    Comprueba si la frecuencia de la columna (freq_columna) cae 
    dentro del rango del canal del dispositivo.
    """
    try:
        metrica = dispositivo.metricas.first() # O la forma en que accedas a la métrica
        if not metrica or not metrica.frequency or not metrica.w_channel:
            return False
        
        f_central = int(metrica.frequency)
        ancho = int(metrica.w_channel)+1
        
        # El rango abarca desde la mitad del ancho hacia abajo hasta la mitad hacia arriba
        inicio = f_central - (ancho / 2)
        fin = f_central + (ancho / 2)
        
        return inicio <= freq_columna < fin
    except (AttributeError, ValueError, TypeError):
        return False

@register.filter
def obtener_metrica(dispositivo, atributo):
    """Obtiene de forma segura el atributo de la métrica relacionada."""
    try:
        metrica = dispositivo.metricas.first()
        return getattr(metrica, atributo, '')
    except Exception:
        return ''
