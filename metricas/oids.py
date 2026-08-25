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
    'if_descr': '1.3.6.1.2.1.2.2.1.2',       # ifTable/ifDescr (walk). MIB-II (RFC1213-MIB / IF-MIB)
    'if_oper': '1.3.6.1.2.1.2.2.1.8',        # ifTable/ifOperStatus (walk). MIB-II (RFC1213-MIB / IF-MIB) current state (1 = up, 2 = down)
    'if_speed': '1.3.6.1.2.1.2.2.1.5',       # ifSpeed (walk). (RFC1213-MIB / IF-MIB) Estimated bandwidth in bits per second.
    #'if_typw': '1.3.6.1.2.1.2.2.1.3',        # ifType (walk) Type of network protocol. 1=other, 2=regular1822, 3=ethernet-card, 24=loopback, 32=frame-relay
    #'if_physadress': '1.3.6.1.2.1.2.2.1.6'   # ifPhysAddress (walk) MAC
    #'if_inerrors': '1.3.6.1.2.1.2.2.1.14'    # ifInErrors (walk) Bad packets received with errors.
    #'if_outerrors': '1.3.6.1.2.1.2.2.1.20'   # ifOutErrors (walk) Outbound packets failing to send.
}

def oids_dispositivo(dispositivo):
    """
    Devuelve el mapa de OIDs combinado para un dispositivo: genéricos + los de su marca.
    """
    # copia limpia del diccionario genérico
    oids = OIDS_GENERICO.copy()

    # Obtenemos directamente la instancia o None
    metric = OIDmetric.objects.filter(marca=dispositivo.marca, tipo='general').first()

    if metric and metric.codigos:
        oids.update(metric.codigos)  # metric.codigos ya es un dict de Python

    #print(oids)
    return oids

def oids_puertos(dispositivo):
    """
    Devuelve los códigos de consulta de los interfaces de red
    """
    # copia limpia del diccionario genérico
    oids = OIDS_PUERTOS_GENERICO.copy()

    # Obtenemos directamente la instancia o None
    metric = OIDmetric.objects.filter(marca=dispositivo.marca, tipo='puertos').first()

    if metric and metric.codigos:
        oids.update(metric.codigos)  # metric.codigos ya es un dict de Python

    #print(oids)
    return oids