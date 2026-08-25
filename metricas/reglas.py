"""
Evaluación de reglas de alarma sobre una métrica recién capturada.

Cada función devuelve `None` si la condición no se cumple o un dict
`{regla, titulo, texto}` con el detalle. El umbral/nivel de cada regla se
configura en `settings.METRICAS_ALARMAS`, salvo el nivel (fijo) que indica
la gravedad para `Evento`.
"""

from eventos.models import Evento
from dispositivos.models import Dispositivo

from .models import DeviceMetrics

# Nivel Evento asociado a cada regla (fijo, no configurable).
REGLA_NIVEL = {
    'sin_respuesta': Evento.Nivel.CRITICAL,
    'onu_offline': Evento.Nivel.CRITICAL,
    'olt_sin_respuesta': Evento.Nivel.CRITICAL,
    'cpu_alta': Evento.Nivel.ERROR,
    'temp_alta': Evento.Nivel.WARNING,
    'puerto_caido': Evento.Nivel.WARNING,
    'sin_clientes_ap': Evento.Nivel.WARNING,
    'cambio_frecuencia': Evento.Nivel.NOTICE,
    'cambio_canal': Evento.Nivel.NOTICE,
    'caida_potencia': Evento.Nivel.WARNING,
    'caida_signal': Evento.Nivel.WARNING,
}

# Reglas que, al cumplirse, marcan el dispositivo como 'inactivo'.
REGLA_INACTIVO = ('sin_respuesta', 'onu_offline', 'olt_sin_respuesta', 'ap_sin_respuesta')


def _conectar_por_tipo(dispositivo):
    """Devuelve la regla de conectividad según el tipo de dispositivo."""

    if dispositivo.tipo.clave == 'olt':
        return 'olt_sin_respuesta'
    if dispositivo.tipo.clave == 'ap':
        return 'ap_sin_respuesta'
    if dispositivo.tipo.clave == 'onu':
        return 'onu_sin_respuesta'
    return 'sin_respuesta'

def evaluar(dispositivo, metrica, anterior, config):
    """
    Devuelve la lista de alarmas 'activas' según la métrica dada.

    - dispositivo: `dispositivos.Dispositivo` monitorizado.
    - metrica: `metricas.DeviceMetrics` recién creada (la actual).
    - anterior: métrica anterior del mismo dispositivo (o None).
    - config: dict `settings.METRICAS_ALARMAS`.
    """
    reglas = []
    conect = _conectar_por_tipo(dispositivo)
    if metrica.status != DeviceMetrics.Status.OK:
        texto = f'{dispositivo.ip_gestion} ({dispositivo.nombre}) no responde a SNMP ({metrica.get_status_display()}).'
        return [{'regla': conect, 'titulo': f'{dispositivo.ip_gestion} {_titulo_conectividad(conect)}', 'texto': texto}]

    if metrica.cpu is not None and metrica.cpu > config['cpu_max']:
        reglas.append({'regla': 'cpu_alta', 'titulo': f'CPU alta {dispositivo.ip_gestion}',
                       'texto': f'CPU al {metrica.cpu:.0f}% (máx. {config["cpu_max"]:.0f}%).'})
        
    if metrica.temperature is not None and metrica.temperature > config['temp_max']:
        reglas.append({'regla': 'temp_alta', 'titulo': f'Temperatura alta {dispositivo.ip_gestion}',
                       'texto': f'Temperatura de {metrica.temperature:.0f} °C (máx. {config["temp_max"]:.0f} °C).'})

    if dispositivo.alarma_puerto:
        if config.get('puerto_caido'):
            caidos = [p['nombre'] for p in metrica.puertos if p.get('estado') == 'down']
            if caidos:
                reglas.append({'regla': 'puerto_caido', 'titulo': f'Puerto caído {dispositivo.ip_gestion}',
                               'texto': f'Interfaz(es) caída(s): {", ".join(caidos)}.'})
            
    if config.get('sin_clientes_ap') and dispositivo.tipo.clave in ('ap','accesp','apoint') \
            and metrica.clients is not None and metrica.clients == 0:
        reglas.append({'regla': 'sin_clientes_ap', 'titulo': f'AP sin clientes {dispositivo.ip_gestion}',
                       'texto': 'Ningún cliente asociado al AP.'})

    if anterior is not None:
        if config.get('cambio_frecuencia') and metrica.frequency is not None \
                and anterior.frequency is not None and metrica.frequency != anterior.frequency:
            reglas.append({'regla': 'cambio_frecuencia', 'titulo': f'Cambio de frecuencia {dispositivo.ip_gestion}',
                           'texto': f'Frecuencia {anterior.frequency:.0f} → {metrica.frequency:.0f} MHz.'})
            
        if config.get('cambio_canal') and metrica.channel and anterior.channel \
                and metrica.channel != anterior.channel:
            reglas.append({'regla': 'cambio_canal', 'titulo': f'Cambio de canal {dispositivo.ip_gestion}',
                           'texto': f'Canal {anterior.channel} → {metrica.channel}.'})
            
        for metrica_campo, regla, titulo, umbral in (
            ('rx_dbm', 'caida_potencia', 'Caída de potencia', config.get('caida_potencia_dbm')),
            ('signal', 'caida_signal', 'Caída de señal', config.get('caida_signal_dbm')),
        ):
            if not umbral:
                continue
            actual, previo = getattr(metrica, metrica_campo), getattr(anterior, metrica_campo)
            if actual is not None and previo is not None:
                caida = previo - actual
                if caida >= umbral:
                    reglas.append({'regla': regla, 'titulo': titulo,
                                   'texto': f'{titulo} de {previo:.0f} a {actual:.0f} dBm.'})
    return reglas


def _titulo_conectividad(regla):
    return {
        'sin_respuesta': 'sin respuesta SNMP',
        'onu_offline': 'ONU offline SNMP',
        'olt_sin_respuesta': 'OLT sin respuesta SNMP',
        'ap_sin_respuesta': 'Acces Point sin respuesta SNMP',
    }.get(regla, 'Fallo de conectividad SNMP')