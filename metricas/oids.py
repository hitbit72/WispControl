"""
Mapa de OIDs SNMP del servicio de monitorización.

Estructura:
- `OIDS_GENERICO`: SNMPv2-MIB / UCD (sistema, memoria, interfaces).
- `OIDS_MIKROTIK`: MIB MTIK (RouterOS) para CPU/RAM/uptime.
- `OIDS_UBNT_AIRMAX`: MIB de Ubiquiti airOS para radio y clientes.

Los OIDs son "básicos" para empezar y se deben validar contra equipos reales
según marca/modelo. Se puede sobrescribir el mapa por dispositivo desde
`Dispositivo.atributos_extra['oids']` (dict métrica -> OID) o ampliar desde
`settings.METRICAS_OIDS_POR_MARCA` para una marca completa.
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

OIDS_UBNT_AIRMAX_ORIGINAL = {
    'signal': '1.3.6.1.4.1.41112.1.4.5.1.1.0',   # señal (dBm)
    'ccq': '1.3.6.1.4.1.41112.1.4.5.1.2.0',      # CCQ (%)
    'rx': '1.3.6.1.4.1.41112.1.4.5.1.3.0',       # tasa Rx (bps)
    'tx': '1.3.6.1.4.1.41112.1.4.5.1.4.0',       # tasa Tx (bps)
    'frequency': '1.3.6.1.4.1.41112.1.4.5.1.5.0',  # frecuencia (MHz)
    'channel': '1.3.6.1.4.1.41112.1.4.5.1.6.0',    # canal
    'clients': '1.3.6.1.4.1.41112.1.4.6.1',        # tabla de estaciones (walk, contar)
    'rx_dbm': '1.3.6.1.4.1.41112.1.4.6.1.7.0',     # Rx dBm de la estación (si aplica)
    'tx_dbm': '1.3.6.1.4.1.41112.1.4.6.1.8.0',     # Tx dBm de la estación (si aplica)
    'snr': '1.3.6.1.4.1.41112.1.4.5.1.7.0',        # SNR (dB)
}


OIDS_UBNT_AIRMAX = {
    'cpu': '1.3.6.1.4.1.10002.1.1.1.4.2.1.3.2',   # 5 Minute Average
    'ccq': '1.3.6.1.4.1.41112.1.4.5.1.7.1',         # UBNT-AirMAX-MIB::ubntWlStatCcq.1
    'clients': '1.3.6.1.4.1.41112.1.4.5.1.15.1',    # UBNT-AirMAX-MIB::ubntWlStatStaCount.1
    'noise': '1.3.6.1.4.1.41112.1.4.5.1.8.1',       # UBNT-AirMAX-MIB::ubntWlStatNoiseFloor
    'power': '1.3.6.1.4.1.41112.1.4.1.1.6.1',       # UBNT-AirMAX-MIB::ubntRadioTxPower
    'signal': '1.3.6.1.4.1.41112.1.4.5.1.5.1',      # UBNT-AirMAX-MIB::ubntWlStatSignal
    'w_channel': '1.3.6.1.4.1.41112.1.4.5.1.14.1',   # width channel
    'rx': '1.3.6.1.4.1.41112.1.4.5.1.10.1',         # tasa Rx (bps) UBNT-AirMAX-MIB::ubntWlStatRxRate
    'tx': '1.3.6.1.4.1.41112.1.4.5.1.9.1',          # tasa Tx (bps) UBNT-AirMAX-MIB::ubntWlStatTxRate
    'frequency': '1.3.6.1.4.1.41112.1.4.1.1.4.1',   # frecuencia (MHz)
    'ssid': '1.3.6.1.4.1.41112.1.4.5.1.2.1',        # nombre ssid
    'antena': '1.3.6.1.4.1.41112.1.4.1.1.9.1',      # tipo de antena instalada
    #'rssi': '1.3.6.1.4.1.41112.1.4.5.1.6.1',        # UBNT-AirMAX-MIB::ubntWlStatRssi
    #'airmax_q': '1.3.6.1.4.1.41112.1.4.6.1.3.1',    # UBNT-AirMAX-MIB::ubntAirMaxQuality
    #'distancia': '1.3.6.1.4.1.41112.1.4.1.1.7.1',   # UBNT-AirMAX-MIB::ubntRadioDistance (metros)
    #'airmax': '1.3.6.1.4.1.41112.1.4.6.1.4.1',      # UBNT-AirMAX-MIB::ubntAirMaxCapacity.1
}

OIDS_UBNT_AF60 = {
    'ram': '1.3.6.1.4.1.41112.1.11.1.2.5.1',     # Memoria %
    'cpu': '1.3.6.1.4.1.41112.1.11.1.2.6.1',        # CPU %
    'frequency': '1.3.6.1.4.1.41112.1.11.1.1.2.1',  # UI-AF60-MIB::af60Frequency
    'w_channel': '1.3.6.1.4.1.41112.1.11.1.1.3.1',      # Ancho de canal
    'ssid': '1.3.6.1.4.1.41112.1.11.1.1.4.1',
    'capacity': '1.3.6.1.4.1.41112.1.11.1.3.1.7.36.90.76.244.78.191.1',     # Total Capacity bps
    'uptime': '1.3.6.1.4.1.41112.1.11.1.2.7.1',                             # Tiempo de ectividad
    'signal': '1.3.6.1.4.1.41112.1.11.1.3.1.3.36.90.76.244.78.191.1',       # Señal local dbm
    #'tx': '1.3.6.1.4.1.41112.1.11.1.3.1.9.36.90.76.244.78.191.1',           # 60GHz TX Bytes
    #'rx': '1.3.6.1.4.1.41112.1.11.1.3.1.10.36.90.76.244.78.191.1',          # 60GHz RX Bytes
    #'ip': '1.3.6.1.4.1.41112.1.11.1.1.5.1',
    #'modelo': '1.3.6.1.4.1.41112.1.11.1.2.3.1',                             # Modelo, largo
    #'signal_r': '1.3.6.1.4.1.41112.1.11.1.3.1.18.36.90.76.244.78.191.1',    # Señal remota dbm
    #'modulacion': '1.3.6.1.4.1.41112.1.11.1.3.1.4.36.90.76.244.78.191.1',   # modulacion de señal
    #'rx_rate': '1.3.6.1.4.1.41112.1.11.1.3.1.5.36.90.76.244.78.191.1',      # RX Data Rate
    #'exp_rx_rate': '1.3.6.1.4.1.41112.1.11.1.3.1.6.36.90.76.244.78.191.1',  # expected RX Data Rate
    #'altitud': '3.6.1.4.1.41112.1.11.1.4.5.1',
}

OIDS_UBNT_AF = {
    'temperatura': '1.3.6.1.4.1.41112.3.2.1.10.1',
    'rx_power0': '1.3.6.1.4.1.41112.3.2.1.11.1',
    'rx_power1': '1.3.6.1.4.1.41112.3.2.1.14.1',
    'enlace': '1.3.6.1.4.1.41112.3.2.1.26.1',
    'eth': '1.3.6.1.4.1.41112.3.2.1.27.1',
    'uptime': '1.3.6.1.4.1.41112.3.2.1.38.1',
    'firmware': '1.3.6.1.4.1.41112.3.2.1.40.1',
    'distancia': '1.3.6.1.4.1.41112.3.2.1.4.1',
    'capacidad_rx': '1.3.6.1.4.1.41112.3.2.1.5.1',
    'capacidad_tx': '1.3.6.1.4.1.41112.3.2.1.6.1',
    'temp_radio0': '1.3.6.1.4.1.41112.3.2.1.8.1',
    'temp_radio1': '1.3.6.1.4.1.41112.3.2.1.10.1',
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

def oids_dispositivo2(dispositivo):
    """
    Devuelve el mapa de OIDs combinado para un dispositivo: genéricos + los de su marca.
    """
    # copia limpia del diccionario genérico
    oids = OIDS_GENERICO.copy()

    # Consultamos solo los campos necesarios de la BD
    # flat=True devuelve una lista plana de los diccionarios JSON: [{}, {}]
    oids_especificos = OIDmetric.objects.filter(
        marca=dispositivo.marca
    ).values_list('codigos', flat=True)

    # Iteramos y fusionamos cada diccionario devuelto
    for codigos_json in oids_especificos:
        if codigos_json:  # Validamos que no sea None o dict vacío
            oids.update(codigos_json)

    # Actualizamos el diccionario directamente con la tuplas (codigos) tipo JSon
    #if oids_especificos:
    #    oids.update(oids_especificos)

    return oids


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