from django import template
from django.utils import timezone
from datetime import datetime, timedelta
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
def formatear_uptime(uptime_val):
    """
    Convierte timeticks de SNMP (centésimas de segundo)
    a formato ejecutable HH:MM:SS o días HH:MM:SS.
    """
    if not uptime_val:
        return "00:00:00"

    horas = 0
    minutos = 0
    segundos = 0

    # Convertir a entero y a segundos reales
    total_segundos = int(uptime_val) // 100

    # timedelta calcula días, horas, minutos y segundos automáticamente
    tiempo = timedelta(seconds=total_segundos)

    # Extraer componentes
    dias = tiempo.days
    horas, rem = divmod(tiempo.seconds, 3600)

    #minutos, segundos = divmod(rem, 3600 % 60)
    # CORRECCIÓN: Dividir 'rem' entre 60 directamente
    minutos, segundos = divmod(rem, 60)

    # Formato corto si tiene días: "175d 15:33:00" | Formato largo si no: "15:33:00"
    if dias > 0:
        return f"{dias}d {horas:02d}:{minutos:02d}:{segundos:02d}"
    
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


@register.filter
def format_bitrate(value):
    try:
        if not value:
            return "—"

        value = int(value)

        if value < 1_000:
            return f"{value} bps"

        elif value < 1_000_000:
            return f"{value / 1_000:.2f} Kbps"

        elif value < 1_000_000_000:
            return f"{value / 1_000_000:.2f} Mbps"

        else:
            return f"{value / 1_000_000_000:.2f} Gbps"

    except (ValueError, TypeError):
        return "—"


@register.filter
def metros_a_km(value):
    km="—"

    try:
        if value:
            value = float(value)
            # Convierte metros a km
            if value < 0:
                return 0
            km = float(value) / 1000
        return f'{km} Km'
    
    except (ValueError, TypeError):
        return "—"
    
@register.filter
def find_station(ip, current_path=None):
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

