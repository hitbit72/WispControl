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

EXCLUDE_PORT = ('lo','ubond','lag','teql','gre','airview','rif','802.1Q','system','encapsulation')
EXCLUDE_PON_PORT = ('eth0','ubond','lag','teql','gre','airview')

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
    contexto = ContextData()

    # debug
    #print(f'Escaneando {dispositivo.ip_gestion}')
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
            #print(f'* --- Escalares uno a uno ({error_st})---')
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
    #print('escalares_uno_a_uno')
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


def consultar_if_table(dispositivo, oids, modo='general'):

    try:
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
        #print(f'{modo} - {dispositivo.ip_gestion}')
        
        # 1. Separar claves ("host", "signal"...) y valores OID ("1.3.6.1...")
        nombres_metricas = list(oids.keys())
        objetos_snmp = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]
        #if modo == 'puertos' and dispositivo.ip_gestion == '192.168.25.150':
        #    print(oids)
        #    print('----------------------')
        #    print(objetos_snmp)

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
                print(f"Error de conexión (Modo: {modo}): {errorIndication}")
                #print(f'ip: {dispositivo.ip_gestion}')
                break
            elif errorStatus:
                print(f"Error SNMP (Modo: {modo}): {errorStatus.prettyPrint()}")
                break
            elif errorIndex:
                print(f"Error SNMP index (Modo: {modo}): {errorIndex}")
                break
            else:
                fila = {}
                # varBinds coincide 1 a 1 en orden con nombres_metricas
                for i, varBind in enumerate(varBinds):
                    oid_respuesta, valor = varBind

                    nombre_clave = nombres_metricas[i]
                    # Convertimos el valor a string limpia
                    fila[nombre_clave] = valor.prettyPrint()

                if modo == 'wifi':
                    #print(f'scan wifi {dispositivo.ip_gestion}')
                    if fila.get('signal'):
                        fila['signal'] = int(fila['signal'])
                    if fila.get('ccq'):
                        fila['ccq'] = int(fila['ccq'])
                        if fila['ccq'] > 100:                  # error de los LiteAP AC, mustra siempre 333 = 33,3
                            fila['ccq'] = fila['ccq'] / 10
                    if fila.get('noise'):
                        fila['noise'] = int(fila['noise'])
                    if fila.get('rx_rate'):
                        fila['rx_rate'] = int(fila['rx_rate'])
                    if fila.get('tx_rate'):
                        fila['tx_rate'] = int(fila['tx_rate'])
                    if fila.get('distancia'):
                        fila['distancia'] = int(fila['distancia'])
                    if fila.get('uptime'):
                        fila['uptime'] = int(fila['uptime'])

                if modo == 'onus':
                    if fila.get('signal'):
                        fila['signal'] = int(fila['signal'])
                        if fila['signal'] < 0:
                            fila['signal']=fila['signal']/100
                    if fila.get('power'):
                        fila['power'] = int(fila['power'])
                        if fila['power'] > 0:
                            fila['power']=fila['power']/100

                # formatear el estado del interfaz
                if modo == 'puertos':
                    #print(fila)
                    fila['estado'] = 'up' if fila['estado'] == '1' else 'down'
                    if fila.get('speed'):
                        if int(fila['speed']) > 1000:
                            #fila['speed'] = int(fila['speed']) * 0.000001   # bps a Mbps
                            fila['speed'] = int(fila['speed']) / 1_000_000   # bps a Mbps
                        else:
                            fila['speed'] = 0
                    else:
                        fila['speed'] = 0
                    #if fila['nombre'] in EXCLUDE_PORT:
                    if any(exclude.lower() in fila['nombre'].lower() for exclude in EXCLUDE_PORT):
                        fila = {}

                if modo == 'puertos_pon':
                    fila['estado'] = 'up' if fila['estado'] == '1' else 'down'
                    if fila.get('speed'):
                        if int(fila['speed']) > 100:
                            fila['speed'] = int(fila['speed']) / 1_000_000   # bps a Mbps
                        else:
                            fila['speed'] = 0
                    else:
                        fila['speed'] = 0

                    #if fila['nombre'] in EXCLUDE_PON_PORT:
                    if any(exclude.lower() in fila['nombre'].lower() for exclude in EXCLUDE_PORT):
                        fila = {}

                if fila:
                    estaciones.append(fila)
    except Exception as e:
        print(f"Error al consultar {dispositivo.ip_gestion} (Modo: {modo}): {e}")
 
    return estaciones