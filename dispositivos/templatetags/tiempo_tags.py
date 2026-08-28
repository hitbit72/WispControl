from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def timestamp_a_transcurrido(value):
    try:
        # Convierte el timestamp numérico a datetime si viene como número
        fecha_pasada = datetime.fromtimestamp(float(value), tz=timezone.get_current_timezone())
        ahora = timezone.now()
        diferencia = ahora - fecha_pasada
        
        dias = diferencia.days
        horas = diferencia.seconds // 3600
        minutos = (diferencia.seconds % 3600) // 60
        
        return f"{dias} días, {horas} horas y {minutos} minutos"
    except (ValueError, TypeError):
        return "Fecha no válida"