"""
Evaluación de reglas de alarma sobre una métrica recién capturada.

Cada función devuelve `None` si la condición no se cumple o un dict
`{regla, titulo, texto}` con el detalle. El umbral/nivel de cada regla se
configura en `settings.METRICAS_ALARMAS`, salvo el nivel (fijo) que indica
la gravedad para `Evento`.
"""

from eventos.models import Evento
from dispositivos.models import Dispositivo, Interfaz

from .models import DeviceMetrics
from dispositivos.models import reglas_ap # Dispositivos que son AP, para cambio de canala

# Nivel Evento asociado a cada regla (fijo, no configurable) -> service.py.
REGLA_NIVEL = {
    'sin_respuesta': Evento.Nivel.WARNING,
    'sin_respuesta_snmp': Evento.Nivel.WARNING,
    'onu_offline': Evento.Nivel.CRITICAL,
    'olt_sin_respuesta': Evento.Nivel.CRITICAL,
    'ap_sin_respuesta': Evento.Nivel.CRITICAL,
    'cpu_alta': Evento.Nivel.ERROR,
    'ram_alta': Evento.Nivel.WARNING,
    'temp_alta': Evento.Nivel.ERROR,
    'puerto_caido': Evento.Nivel.WARNING,
    'puerto_recuperado': Evento.Nivel.NOTICE,
    'sin_clientes_ap': Evento.Nivel.NOTICE,
    'cambio_frecuencia': Evento.Nivel.WARNING,
    'caida_potencia_rx': Evento.Nivel.WARNING,
    'caida_potencia_tx': Evento.Nivel.WARNING,
    'caida_signal': Evento.Nivel.WARNING,
    'ping_sin_respuesta': Evento.Nivel.CRITICAL,
    'ping_recuperado': Evento.Nivel.NOTICE,
}

def _texto_conectividad(tipo):
    return f'Dispositivo {tipo} sin respuesta SNMP'

def evaluar(dispositivo, metrica, metrica_anterior, historico, historico_anterior, config):
    """
    Devuelve la lista de alarmas 'activas' según la métrica dada.

    - dispositivo: `dispositivos.Dispositivo` monitorizado.
    - metrica: `metricas.DeviceMetrics` recién creada (la actual).
    - metrica_anterior: métrica anterior del mismo dispositivo (o None).
    - historico: metrica historica altual
    - hisotrico_anterior: metrica historica anterior
    - config: dict `settings.METRICAS_ALARMAS`.
    """
    reglas = []

    if metrica.status != DeviceMetrics.Status.OK:
        texto = f'{dispositivo.nombre} no responde a SNMP ({metrica.get_status_display()}).'
        return [{'regla': 'sin_respuesta_snmp', 'titulo': f'Sin respuesta SNMP {dispositivo.ip_gestion}', 'texto': texto}]

    if historico.cpu is not None and historico.cpu > config['cpu_max']:
        #print(f'CPU alta {dispositivo.ip_gestion}')
        reglas.append({'regla': 'cpu_alta', 'titulo': f'CPU alta {historico.cpu:.0f}% · {dispositivo.ip_gestion}',
                       'texto': f'{dispositivo.nombre}. La CPU del dispositivo esta al {historico.cpu:.0f}% (máx. {config["cpu_max"]:.0f}%).'})

    if historico.ram is not None and historico.ram > config['ram_max']:
        #print(f'RAM alta {dispositivo.ip_gestion}')
        reglas.append({'regla': 'ram_alta', 'titulo': f'RAM alta {historico.ram:.0f}% · {dispositivo.ip_gestion}',
                       'texto': f'{dispositivo.nombre}. La RAM del dispositivo esta al {historico.ram:.0f}% (máx. {config["ram_max"]:.0f}%).'})
        
    if historico.temperature is not None and historico.temperature > config['temp_max']:
        reglas.append({'regla': 'temp_alta', 'titulo': f'Temperatura alta {historico.temperature:.0f} °C · {dispositivo.ip_gestion}',
                       'texto': f'{dispositivo.nombre}. La Temperatura del dispositivos es alta {historico.temperature:.0f} °C (máx. {config["temp_max"]:.0f} °C).'})

    """
    if dispositivo.alarma_puerto:
        if config.get('puerto_caido'):
            caidos = [p['nombre'] for p in metrica.puertos if p.get('estado') == 'down']
            if caidos:
                reglas.append({'regla': 'puerto_caido', 'titulo': f'Puerto caído {dispositivo.ip_gestion}',
                               'texto': f'{dispositivo.nombre}. Interfaz(es) caída(s): {", ".join(caidos)}.'})
    """

    # Comprobación de los puertos del dispositivo
    if dispositivo.alarma_puerto and metrica_anterior is not None and getattr(metrica_anterior, 'puertos', None):

        # 1. Creamos el diccionario de forma más limpia usando un diccionario por comprensión
        nPuerto = {
            mport['nombre']: {'estado': mport['estado'], 'speed': mport['speed']} 
            for mport in metrica_anterior.puertos
        }
        
        # 2. Obtenemos las interfaces con alarma, filtramos directamente de la BD
        interfaces = Interfaz.objects.filter(dispositivo=dispositivo, alarma_cambio=True)
        
        # 3. Comprobamos los cambios recorriendo solo las que tienen la alarma activa
        for iface in interfaces:
            # Usamos .get() para evitar un KeyError si el nombre de la interfaz no existía previamente
            port_anterior = nPuerto.get(iface.nombre)
            
            if port_anterior and port_anterior['estado'] != iface.estado:
                if iface.estado == 'down': # O comparando con port_anterior['estado'] == 'up' dependiendo de la lógica de cambio
                    regla_tipo = 'puerto_caido'
                    titulo = f'Interface caido {dispositivo.ip_gestion}'
                    texto = f'{dispositivo.nombre}. Interfaz desconectado: {iface.nombre}'
                else:
                    regla_tipo = 'puerto_recuperado' # O 'puerto_recuperado' según tu app
                    titulo = f'Interface recuperado {dispositivo.ip_gestion}'
                    texto = f'{dispositivo.nombre}. Interfaz conectado: {iface.nombre}'
                    
                reglas.append({'regla': regla_tipo, 'titulo': titulo, 'texto': texto})

            elif port_anterior and iface.estado == 'up':
                if iface.velocidad_mbps != port_anterior['speed']:
                    regla_tipo = 'puerto_caido'
                    titulo = f'Error en Interface {dispositivo.ip_gestion}'
                    texto = f'{dispositivo.nombre}. Interfaz con velocidad incorrecta: {iface.nombre} - {iface.velocidad_mbps} Mbps'
                    reglas.append({'regla': regla_tipo, 'titulo': titulo, 'texto': texto})


    if config.get('sin_clientes_ap') and dispositivo.tipo.clave in reglas_ap \
            and metrica.clients is not None and metrica.clients == 0:
        reglas.append({'regla': 'sin_clientes_ap', 'titulo': f'AP sin clientes {dispositivo.ip_gestion}',
                       'texto': f'{dispositivo.nombre}. Ningún cliente asociado al AP.'})

    if metrica_anterior is not None:
        if dispositivo.tipo.clave in reglas_ap:
            if config.get('cambio_frecuencia') and metrica.frequency is not None \
                    and dispositivo.frequency is not None and metrica.frequency != dispositivo.frequency:
                reglas.append({'regla': 'cambio_frecuencia', 'titulo': f'Cambio de frecuencia {dispositivo.ip_gestion}',
                            'texto': f'{dispositivo.nombre}. Frecuencia {dispositivo.frequency:.0f} → {metrica.frequency:.0f} MHz.'})
                
        for historico_campo, regla, titulo, medida, umbral in (
            ('signal', 'caida_signal', 'Caída de señal', 'dBm', config.get('caida_signal_dbm')),
            ('power', 'caida_potencia_tx', 'Caída de potencia TX', 'dBm', config.get('caida_potencia_tx')),
        ):
            if not umbral:
                continue
            if regla == 'caida_signal' and metrica.clients == 0:
                continue
            
            actual = None
            previo = None 
            if historico and historico_anterior:
                actual, previo = getattr(historico, historico_campo), getattr(historico_anterior, historico_campo)
            if actual is not None and previo is not None and actual != 0 and  previo != 0:
                if actual == previo:
                    continue
                caida = previo - actual
                if caida >= umbral:
                    reglas.append({'regla': regla, 'titulo': f'{titulo} {dispositivo.ip_gestion} ({actual:.0f} {medida})',
                                   'texto': f'{dispositivo.nombre}. {titulo} de {previo:.0f} a {actual:.0f} {medida}.'})
    return reglas

