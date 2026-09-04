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
    'sin_respuesta': Evento.Nivel.WARNING,
    'sin_respuesta_snmp': Evento.Nivel.WARNING,
    'onu_offline': Evento.Nivel.CRITICAL,
    'olt_sin_respuesta': Evento.Nivel.CRITICAL,
    'ap_sin_respuesta': Evento.Nivel.CRITICAL,
    'cpu_alta': Evento.Nivel.ERROR,
    'ram_alta': Evento.Nivel.WARNING,
    'temp_alta': Evento.Nivel.WARNING,
    'puerto_caido': Evento.Nivel.WARNING,
    'sin_clientes_ap': Evento.Nivel.NOTICE,
    'cambio_frecuencia': Evento.Nivel.ERROR,
    'cambio_canal': Evento.Nivel.ERROR,
    'caida_potencia_rx': Evento.Nivel.WARNING,
    'caida_potencia_tx': Evento.Nivel.WARNING,
    'caida_signal': Evento.Nivel.WARNING,
    'ping_sin_respuesta': Evento.Nivel.CRITICAL,
    'ping_recuperado': Evento.Nivel.NOTICE,
}

def _texto_conectividad(tipo):
    return f'Dispositivo {tipo} sin respuesta SNMP'

def evaluar(dispositivo, metrica, anterior, config):
    """
    Devuelve la lista de alarmas 'activas' según la métrica dada.

    - dispositivo: `dispositivos.Dispositivo` monitorizado.
    - metrica: `metricas.DeviceMetrics` recién creada (la actual).
    - anterior: métrica anterior del mismo dispositivo (o None).
    - config: dict `settings.METRICAS_ALARMAS`.
    """
    reglas = []

    if metrica.status != DeviceMetrics.Status.OK:
        texto = f'{dispositivo.ip_gestion} ({dispositivo.nombre}) no responde a SNMP ({metrica.get_status_display()}).'
        return [{'regla': 'sin_respuesta_snmp', 'titulo': f'{dispositivo.ip_gestion} {_texto_conectividad(dispositivo.tipo.nombre)}', 'texto': texto}]

    if metrica.cpu is not None and metrica.cpu > config['cpu_max']:
        #print(f'CPU alta {dispositivo.ip_gestion}')
        reglas.append({'regla': 'cpu_alta', 'titulo': f'CPU alta {metrica.cpu:.0f}% · {dispositivo.ip_gestion}',
                       'texto': f'La CPU del dispositivo esta al {metrica.cpu:.0f}% (máx. {config["cpu_max"]:.0f}%).'})

    if metrica.ram is not None and metrica.ram > config['ram_max']:
        #print(f'RAM alta {dispositivo.ip_gestion}')
        reglas.append({'regla': 'ram_alta', 'titulo': f'RAM alta {metrica.ram:.0f}% · {dispositivo.ip_gestion}',
                       'texto': f'La RAM del dispositivo esta al {metrica.ram:.0f}% (máx. {config["ram_max"]:.0f}%).'})
        
    if metrica.temperature is not None and metrica.temperature > config['temp_max']:
        reglas.append({'regla': 'temp_alta', 'titulo': f'Temperatura alta {metrica.temperature:.0f} °C · {dispositivo.ip_gestion}',
                       'texto': f'La Temperatura del dispositivos es alta {metrica.temperature:.0f} °C (máx. {config["temp_max"]:.0f} °C).'})

    if dispositivo.alarma_puerto:
        if config.get('puerto_caido'):
            caidos = [p['nombre'] for p in metrica.puertos if p.get('estado') == 'down']
            if caidos:
                reglas.append({'regla': 'puerto_caido', 'titulo': f'Puerto caído {dispositivo.ip_gestion}',
                               'texto': f'Interfaz(es) caída(s): {", ".join(caidos)}.'})
            
    if config.get('sin_clientes_ap') and dispositivo.tipo.clave in ('ap','accesp','apoint','olt') \
            and metrica.clients is not None and metrica.clients == 0:
        reglas.append({'regla': 'sin_clientes_ap', 'titulo': f'AP sin clientes {dispositivo.ip_gestion}',
                       'texto': 'Ningún cliente asociado al AP.'})

    if anterior is not None:
        if config.get('cambio_frecuencia') and metrica.frequency is not None \
                and dispositivo.frequency is not None and metrica.frequency != dispositivo.frequency:
            reglas.append({'regla': 'cambio_frecuencia', 'titulo': f'Cambio de frecuencia {dispositivo.ip_gestion}',
                           'texto': f'Frecuencia {dispositivo.frequency:.0f} → {metrica.frequency:.0f} MHz.'})
            
        if config.get('cambio_canal') and metrica.channel and anterior.channel \
                and metrica.channel != anterior.channel:
            reglas.append({'regla': 'cambio_canal', 'titulo': f'Cambio de canal {dispositivo.ip_gestion}',
                           'texto': f'Canal {anterior.channel} → {metrica.channel}.'})
            
        for metrica_campo, regla, titulo, umbral in (
            ('rx_dbm', 'caida_potencia_rx', 'Caída de potencia RX', config.get('caida_potencia_rx')),
            ('signal', 'caida_signal', 'Caída de señal', config.get('caida_signal_dbm')),
            ('power', 'caida_potencia_tx', 'Caída de potencia TX', config.get('caida_potencia_tx')),
        ):
            if not umbral:
                continue
            actual, previo = getattr(metrica, metrica_campo), getattr(anterior, metrica_campo)
            if actual is not None and previo is not None:
                caida = previo - actual
                if caida >= umbral:
                    reglas.append({'regla': regla, 'titulo': f'{titulo} {dispositivo.ip_gestion} ({actual:.0f})',
                                   'texto': f'{titulo} de {previo:.0f} a {actual:.0f} dBm.'})
    return reglas

