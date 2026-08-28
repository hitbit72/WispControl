"""
Cliente SNMP del servicio de monitorización (pysnmp-lextudio).

Expone helpers simples sobre la API clásica síncrona de pysnmp:
- `consultar_escalares(dispositivo, oids)`: GET múltiple de OIDs escalares.
- `consultar_if_table(dispositivo)`: estado de interfaces (ifTable, walk).

El transporte se configura por dispositivo desde
`Dispositivo.atributos_extra['snmp']` (puerto, timeout, reintentos), con los
valores por defecto de `settings.METRICAS_SNMP`.
"""

import django.conf as _conf

from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    nextCmd,
)


MODO_IPV4 = 0  # CommunityData(mpModel=0) mpModel=0 para SNMPv1, 1 para SNMPv2c

OID_IF_DESCR = '1.3.6.1.2.1.2.2.1.2'
OID_IF_OPER = '1.3.6.1.2.1.2.2.1.8'
OID_IF_SPEED = '1.3.6.1.2.1.2.2.1.5'
OID_IF_TYPE = '1.3.6.1.2.1.2.2.1.3' 

EXCLUDE_PORT = ('lo','ubond','ubond0','lag','lag1')

# IF_TYPE
# 6 (ethernetCsmacd): Redes Ethernet estándar.
# 24 (softwareLoopback): Interfaz virtual de bucle local (loopback).
# 71 (ieee80211): Interfaces inalámbricas (Wi-Fi) en equipos D-Link antiguos o puntos

# ErrorStatus que significan "el OID no existe" (no fallo de comunicaciones).
_FALTA_OID = ('nosuchname', 'nosuchobject', 'nosuchinstance')

class SnmpError(Exception):
    """Error de consulta SNMP (sin respuesta, protocolo, etc.)."""


def _objetos(oid):
    return ObjectType(ObjectIdentity(oid))


def _valor_numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        try:
            return float(str(valor))
        except ValueError:
            return None


def _valor_texto(valor):
    try:
        texto = str(valor.prettyPrint())
    except AttributeError:
        texto = str(valor)
    if texto.startswith('No Such Object') or texto.startswith('No Such Instance'):
        return ''
    return texto


def _conf_snmp(dispositivo):
    conf = dict(_conf.settings.METRICAS_SNMP)
    snmp = (dispositivo.atributos_extra or {}).get('snmp') or {}
    conf.update(snmp)
    return conf


def _trasporte(host, conf):
    return UdpTransportTarget(
        (host, int(conf['puerto'])),
        timeout=float(conf['timeout']),
        retries=int(conf['reintentos']),
    )


def _auth(comunidad):
    return CommunityData(comunidad, mpModel=MODO_IPV4)

def _es_falta_oid(error_st):
    try:
        nombre = error_st.prettyPrint().lower()
    except AttributeError:
        nombre = str(error_st).lower()
    return nombre in _FALTA_OID

def consultar_escalares(dispositivo, oids):
    """GET múltiple: dict métrica -> OID. Devuelve dict métrica ->
    (valor_numero, valor_texto). Los OIDs sin soporte se omiten. Lanza
    SnmpError si el equipo no responde o da error de protocolo."""
    if not oids:
        return {}
    conf = _conf_snmp(dispositivo)
    comunidad = dispositivo.snmp_community or 'public'
    engine = SnmpEngine()
    transporte = _trasporte(dispositivo.ip_gestion, conf)
    print(f'Escaneando {dispositivo.ip_gestion}')
    contexto = ContextData()

    # debug
    #print(transporte)
    #print(comunidad)
    #print(oids)
    
    error_ind, error_st, error_idx, var_binds = next(
        getCmd(
            engine, _auth(comunidad), transporte, contexto,
            *[_objetos(oid) for oid in oids.values()],
        )
    )
    if error_ind:
        raise SnmpError(str(error_ind))

    # Un agente SNMPv1 devuelve noSuchName para TODO el GET si un solo OID
    # no existe. En ese caso se reintenta cada OID por separado.
    if error_st:
        if _es_falta_oid(error_st):
            # debug
            print(f'* --- Escalares uno a uno ({error_st})---')
            #print(oids)
            return _escalares_uno_a_uno(engine, _auth(comunidad), transporte, contexto, oids)
        raise SnmpError(error_st.prettyPrint())

    resultado = {}
    for (oid, valor), metrica in zip(var_binds, oids):
        texto = _valor_texto(valor)
        if not texto:
            continue
        resultado[metrica] = (_valor_numero(valor), texto)
    return resultado

def _escalares_uno_a_uno(engine, auth, transporte, contexto, oids):
    print('escalares_uno_a_uno')
    resultado = {}
    for metrica, oid in oids.items():
        error_ind, error_st, _, var_binds = next(
            getCmd(engine, auth, transporte, contexto, _objetos(oid))
        )
        if error_ind:
            raise SnmpError(str(error_ind))
        if error_st:
            if _es_falta_oid(error_st):
                continue
            raise SnmpError(error_st.prettyPrint())
        for _oid, valor in var_binds:
            texto = _valor_texto(valor)
            if not texto:
                continue
            resultado[metrica] = (_valor_numero(valor), texto)
    return resultado


def consultar_if_table2(dispositivo, oids):
    """Walk de ifTable (descr + oper status). Devuelve lista de
    {nombre, estado} con estado 'up'/'down'."""
    if not oids:
        return []
    
    conf = _conf_snmp(dispositivo)
    comunidad = dispositivo.snmp_community or 'public'
    comunity = _auth(comunidad)
    engine = SnmpEngine()
    transporte = _trasporte(dispositivo.ip_gestion, conf)
    contexto = ContextData()
    puertos = []

    """
    OIDs base a consultar en IF-MIB
    1.3.6.1.2.1.2.2.1.2 = ifDescr (Nombre del puerto)
    1.3.6.1.2.1.2.2.1.5 = ifSpeed (Velocidad en bps)
    1.3.6.1.2.1.2.2.1.8 = ifOperStatus (Estado operativo: 1=Up, 2=Down)
    """

    # Toma el OID del diccionario o usa la constante por defecto si no existe en 'oids'
    oid_descr = ObjectType(ObjectIdentity(oids.get('nombre', OID_IF_DESCR)))
    oid_status = ObjectType(ObjectIdentity(oids.get('estado', OID_IF_OPER)))
    oid_speed = ObjectType(ObjectIdentity(oids.get('speed', OID_IF_SPEED)))

    # Usamos nextCmd para hacer un walk sobre las 3 columnas simultáneamente
    for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
        engine,
        comunity,
        transporte,
        contexto,
        oid_descr,
        oid_speed,
        oid_status,
        lexicographicMode=False,
    ):
        if errorIndication:
            print(f"Error de conexión: {errorIndication}")
            break
        elif errorStatus:
            print(f"Error SNMP: {errorStatus.prettyPrint()}")
            break
        else:
            # Extraer los datos de la fila actual
            interface_name = str(varBinds[0][1])
            speed_bps = int(varBinds[1][1])
            status_code = int(varBinds[2][1])
            
            # Formatear el estado y la velocidad
            status_str = "up" if status_code == 1 else "down"
            speed_mbps = speed_bps // 1_000_000 if speed_bps > 0 else 0

            #print(f"Interfaz: {interface_name:<10} | Estado: {status_str:<18} | Velocidad: {speed_mbps} Mbps")
            # Comprueba si NINGUNO de los patrones en EXCLUDE_PORT está contenido en interface_name
            if not any(excluir in interface_name for excluir in EXCLUDE_PORT):
                puertos.append({
                    'nombre': interface_name,
                    'estado': status_str,
                    'speed': speed_mbps,
                })
    return puertos


def consultar_if_table(dispositivo, oids, modo='general'):

    if not oids:
        return []
    #print(f"Total OIDs a consultar: {len(oids)}")
    #print(oids)

    # Consulta las staciones conectadas a un AP o una OLT
    conf = _conf_snmp(dispositivo)
    comunidad = dispositivo.snmp_community or 'public'
    comunity = _auth(comunidad)
    engine = SnmpEngine()
    transporte = _trasporte(dispositivo.ip_gestion, conf)
    contexto = ContextData()
    estaciones = []

    # 1. Separar claves ("host", "signal"...) y valores OID ("1.3.6.1...")
    nombres_metricas = list(oids.keys())
    objetos_snmp = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]

    # Usamos nextCmd para hacer un walk sobre las 3 columnas simultáneamente
    for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
        engine,
        comunity,
        transporte,
        contexto,
        *objetos_snmp,  # <-- Pasa todas las columnas juntas
        lexicographicMode=False,
    ):
        if errorIndication:
            print(f"Error de conexión: {errorIndication}")
            break
        elif errorStatus:
            print(f"Error SNMP: {errorStatus.prettyPrint()}")
            break
        else:
            fila = {}
            # varBinds coincide 1 a 1 en orden con nombres_metricas
            for i, varBind in enumerate(varBinds):
                oid_respuesta, valor = varBind
                nombre_clave = nombres_metricas[i]

                # Convertimos el valor a string limpia
                valor_str = valor.prettyPrint()

                # formatear el estado del interfaz
                """
                if modo == 'puertos':
                    if nombre_clave == 'estado':
                        print(f'{nombre_clave}: {valor_str} ')
                        valor_str = 'up' if valor_str == '1' else 'down'
                """
                fila[nombre_clave] = valor_str

            if modo == 'puertos':
                #print(fila)
                fila['estado'] = 'up' if fila['estado'] == '1' else 'down'
                if int(fila['speed']) > 100:
                    fila['speed'] = int(fila['speed']) * 0.000001
                else:
                    fila['speed'] = 0
                if fila['nombre'] in EXCLUDE_PORT:
                    fila = {}

            if fila:
                estaciones.append(fila)

    return estaciones