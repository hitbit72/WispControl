from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe  # <-- Importa esto
from urllib.parse import urlencode # Para formatear correctamente la URL

from dispositivos.models import Dispositivo

register = template.Library()


@register.simple_tag  # <-- Cambiamos a simple_tag
def find_onu(serial, cliente, current_path=None):
    # Busca la ONU asociada a esta OLT
    # Se podria usar la función 'find_station', cambiandola a @register.simple_tag,
    # y añadiendo un parametro más como tipo='wifi o onu'

    html = f'<td>—</td><td>{cliente}</td>'
    if not serial:
        return mark_safe(html)

    ip=serial
    dispositivo = Dispositivo.objects.filter(onu_ref=serial).first()
    if dispositivo:
        url_cliente = reverse('clientes:detalle', args=[dispositivo.cliente.pk])
        url_stacion = reverse('dispositivos:detalle', args=[dispositivo.pk])
        if dispositivo.ip_gestion:
            ip = dispositivo.ip_gestion
            
        # Si nos pasaron la ruta actual, añadimos el ?next=
        if current_path:
            querystring = urlencode({'next': current_path})
            url_cliente = f"{url_cliente}?{querystring}"
            url_stacion = f"{url_stacion}?{querystring}"

        # Envolvemos el string con mark_safe para renderizar como HTML real
        html = f'<td><a href="{url_stacion}">{ip}</a></td><td><a href="{url_cliente}">{dispositivo.cliente.nombre_completo}</a></td>'
        return mark_safe(html)

    html = f'<td>{ip}</td><td>{cliente}</td>'
    return mark_safe(html)