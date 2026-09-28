from django.test import TestCase

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


def _conf_snmp(cm):
    conf = dict(_conf.settings.METRICAS_SNMP)
    snmp = (cm)
    conf.update(snmp)
    return conf

def _trasporte(host, conf):
    return UdpTransportTarget(
        (host, int(conf['puerto'])),
        timeout=float(conf['timeout']),
        retries=int(conf['reintentos']),
    )



oid1 = {
"ip": "1.3.6.1.4.1.41112.1.4.7.1.10.1", 
"ccq": "1.3.6.1.4.1.41112.1.4.7.1.6.1", 
"host": "1.3.6.1.4.1.41112.1.4.7.1.2.1", 
"noise": "1.3.6.1.4.1.41112.1.4.7.1.4.1", 
"signal": "1.3.6.1.4.1.41112.1.4.7.1.3.1", 
"uptime": "1.3.6.1.4.1.41112.1.4.7.1.15.1", 
"rx_rate": "1.3.6.1.4.1.41112.1.4.7.1.11.1",
"tx_rate": "1.3.6.1.4.1.41112.1.4.7.1.12.1",
"distancia": "1.3.6.1.4.1.41112.1.4.7.1.5.1"
}

oid2 = {
"ip": "1.3.6.1.4.1.41112.1.4.7.1.10.1", 
"ccq": "1.3.6.1.4.1.41112.1.4.7.1.6.1", 
"host": "1.3.6.1.4.1.41112.1.4.7.1.2.1", 
"noise": "1.3.6.1.4.1.41112.1.4.7.1.4.1", 
"signal": "1.3.6.1.4.1.41112.1.4.7.1.3.1", 
"uptime": "1.3.6.1.4.1.41112.1.4.7.1.15.1", 
"rx_rate": "1.3.6.1.4.1.41112.1.4.7.1.11.1",
"tx_rate": "1.3.6.1.4.1.41112.1.4.7.1.12.1",
"distancia": "1.3.6.1.4.1.41112.1.4.7.1.5.1",
"count_tx": "1.3.6.1.4.1.41112.1.4.7.1.13.1",
"count_rx": "1.3.6.1.4.1.41112.1.4.7.1.14.1"
}

oid3 = {"count_tx": "1.3.6.1.4.1.41112.1.4.7.1.13.1", "count_rx": "1.3.6.1.4.1.41112.1.4.7.1.14.1"}

ip = '192.168.25.158'
comunidad = 'inforcem'
conf = _conf_snmp(comunidad)
engine = SnmpEngine()
transporte = _trasporte(ip, conf)
contexto = ContextData()


#nombres_metricas = list(oid1.keys())
#objetos_snmp = [ObjectType(ObjectIdentity(oid)) for oid in oid1.values()]

"""
iterator = getCmd(
    SnmpEngine(),
    CommunityData(comunidad),
    UdpTransportTarget((ip, 161)),
    ContextData(),
    *[
        ObjectType(ObjectIdentity(oid))
        for oid in oid1.values()
    ]
)
"""

iterator = getCmd(
    engine,
    CommunityData(comunidad),
    transporte,
    ContextData(),
    *[
        ObjectType(ObjectIdentity(oid))
        for oid in oid1.values()
    ]
)

#snmpget -v1 -c inforcem 192.168.25.158 1.3.6.1.4.1.41112.1.4.7.1.13.1