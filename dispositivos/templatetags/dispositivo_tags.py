from django import template
from django.utils import timezone
from datetime import datetime
from django.urls import reverse
from django.utils.safestring import mark_safe  # <-- Importa esto
from urllib.parse import urlencode # Para formatear correctamente la URL

from dispositivos.models import Dispositivo

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


@register.filter
def bps_a_mbps(value):
    try:
        # Convierte bps a mbps (# 1bsp = 0,000001 mbps)
        if value < 1000:
            return value
        bps = int(value) * 0.000001
        return bps
    
    except (ValueError, TypeError):
        return "Error"


@register.filter
def find_client(ip, current_path=None):
    # Busca una estacion a partir de su ip

    if not ip:
        return mark_safe('<td>—</td><td>—</td>')
    
    dispositivo = Dispositivo.objects.filter(ip_gestion=ip).first()
    if dispositivo:
        url_cliente = reverse('clientes:detalle', args=[dispositivo.cliente.pk])
        url_stacion = reverse('dispositivos:detalle', args=[dispositivo.pk])

        # Si nos pasaron la ruta actual, añadimos el ?next=
        if current_path:
            querystring = urlencode({'next': current_path})
            url_cliente = f"{url_cliente}?{querystring}"
            url_stacion = f"{url_stacion}?{querystring}"

        # Envolvemos el string con mark_safe para renderizar como HTML real
        html = f'<td><a href="{url_stacion}">{ip}</a></td><td><a href="{url_cliente}">{dispositivo.cliente.nombre_completo}</a></td>'
        return mark_safe(html)

    html = f'<td>{ip}</td><td>—</td>'
    return mark_safe(html)
    
