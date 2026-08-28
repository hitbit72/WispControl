"""
Mapa de OIDs SNMP del servicio de monitorización.
Se usan los OIDs 'genéricos' para empezar y se combina con
los de latabla 'OIDmetric' para cada Marca y modelo

Los OIDs son "básicos" para empezar y se deben validar contra equipos reales
según marca/modelo.
"""

from django.conf import settings
from dispositivos.models import Marca
from metricas.models import OIDmetric

"""

Clientes del AP AirMax (M5/Rocket)
{"ip": "1.3.6.1.4.1.41112.1.4.7.1.10.1", 
"ccq": "1.3.6.1.4.1.41112.1.4.7.1.6.1", 
"host": "1.3.6.1.4.1.41112.1.4.7.1.2.1", 
"noise": "1.3.6.1.4.1.41112.1.4.7.1.4.1", 
"signal": "1.3.6.1.4.1.41112.1.4.7.1.3.1", 
"mac": "1.3.6.1.4.1.41112.1.4.7.1.1.1", 
"rx_rate": "1.3.6.1.4.1.41112.1.4.7.1.11.1", 
"tx_rate": "1.3.6.1.4.1.41112.1.4.7.1.12.1"}
"""

OIDS_MIKROTIK = {
    'cpu': '1.3.6.1.4.1.14988.1.1.1.2.1.1.0',      # mtikSystemCpu (%)
    'mem_libre': '1.3.6.1.4.1.14988.1.1.1.2.1.2.0',  # mtikSystemFreeMemory
    'mem_total': '1.3.6.1.4.1.14988.1.1.1.2.1.3.0',  # mtikSystemTotalMemory
    #'uptime': '1.3.6.1.4.1.14988.1.1.1.2.1.4.0',     # mtikSystemUptime (segundos)
}


OIDS_GENERICO = {
    'uptime': '1.3.6.1.2.1.1.3.0',           # sysUpTime (hundredths de segundo)
    'sys_name': '1.3.6.1.2.1.1.5.0',         #sysName
    'sys_descr': '1.3.6.1.2.1.1.1.0',        #sysDescription
    #'cpu': '1.3.6.1.4.1.2021.10.1.3.2',      # 5min load average. UCD-SNMP-MIB
    #'mem_total': '1.3.6.1.4.1.2021.4.5.0',   # memTotalReal (bytes) - UCD
    #'mem_libre': '1.3.6.1.4.1.2021.4.6.0',   # memAvailReal (bytes) - UCD
}

OIDS_PUERTOS_GENERICO = {
    'nombre': '1.3.6.1.2.1.2.2.1.2',       # ifTable/ifDescr (walk). MIB-II (RFC1213-MIB / IF-MIB)
    'estado': '1.3.6.1.2.1.2.2.1.8',        # ifTable/ifOperStatus (walk). MIB-II (RFC1213-MIB / IF-MIB) current state (1 = up, 2 = down)
    'speed': '1.3.6.1.2.1.2.2.1.5',       # ifSpeed (walk). (RFC1213-MIB / IF-MIB) Estimated bandwidth in bits per second.
    #'if_rx': '1.3.6.1.2.1.2.2.1.10',
    #'if_tx': '1.3.6.1.2.1.2.2.1.11',
    #'if_typw': '1.3.6.1.2.1.2.2.1.3',        # ifType (walk) Type of network protocol. 1=other, 2=regular1822, 3=ethernet-card, 24=loopback, 32=frame-relay
    #'if_physadress': '1.3.6.1.2.1.2.2.1.6'   # ifPhysAddress (walk) MAC
    #'if_inerrors': '1.3.6.1.2.1.2.2.1.14'    # ifInErrors (walk) Bad packets received with errors.
    #'if_outerrors': '1.3.6.1.2.1.2.2.1.20'   # ifOutErrors (walk) Outbound packets failing to send.
}

def oids_dispositivo(dispositivo, tipos='general'):
    """
    Devuelve el mapa de OIDs combinado para un dispositivo: genéricos + los de su marca.
    """

    # Obtenemos directamente la instancia
    metric = OIDmetric.objects.filter(marca=dispositivo.marca, tipo=tipos).first()

    # 'general' y 'puertos' tienen codigos genericos
    if tipos == 'general':
        # copia limpia del diccionario genérico
        oids = OIDS_GENERICO.copy()
        if metric and metric.codigos:
            oids.update(metric.codigos)  # metric.codigos ya es un dict de Python
        return oids
    elif tipos == 'puertos':
        oids = OIDS_PUERTOS_GENERICO.copy()
        if metric and metric.codigos:
            oids.update(metric.codigos)
        return oids
    
    #print(oids)
    if metric and metric.codigos:
        return metric.codigos
    else:
        return {}

    