from django.test import TestCase
import django.conf as _conf


"""
Pruebas SNMP para dispositivos Ubiquiti.

Objetivo:
    Comprobar el comportamiento de nextCmd() con las columnas
    SNMP normales y las columnas Counter64:

        .13.1 = ubntStaTxBytes
        .14.1 = ubntStaRxBytes

Requisitos:
    pysnmp-lextudio>=5.0.6,<6.0.0
    pyasn1==0.6.0

Uso:
    python test_snmp.py
    python metricas/test_snmp.py
o:
    uv run tests.py
"""

from pysnmp.hlapi import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    nextCmd,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

IP = "192.168.25.158"
COMMUNITY = "inforcem"
PORT = 161


# ============================================================
# OID BASE
# ============================================================

BASE = "1.3.6.1.4.1.41112.1.4.7.1"


OID = {
    "ip":        f"{BASE}.10.1",
    "ccq":       f"{BASE}.6.1",
    "host":      f"{BASE}.2.1",
    "noise":     f"{BASE}.4.1",
    "signal":    f"{BASE}.3.1",
    "uptime":    f"{BASE}.15.1",
    "rx_rate":   f"{BASE}.11.1",
    "tx_rate":   f"{BASE}.12.1",
    "distancia": f"{BASE}.5.1",

    # Counter64
    "count_tx":  f"{BASE}.13.1",
    "count_rx":  f"{BASE}.14.1",
}


# ============================================================
# GRUPOS DE PRUEBA
# ============================================================

PRUEBAS = {

    # Solo Counter64 TX
    "1 - Solo count_tx": [
        "count_tx",
    ],

    # Solo Counter64 RX
    "2 - Solo count_rx": [
        "count_rx",
    ],

    # Los dos Counter64
    "3 - count_tx + count_rx": [
        "count_tx",
        "count_rx",
    ],

    # Columnas originales
    "4 - Columnas originales": [
        "ip",
        "ccq",
        "host",
        "noise",
        "signal",
        "uptime",
        "rx_rate",
        "tx_rate",
        "distancia",
    ],

    # Todas las columnas
    "5 - Todas las columnas": [
        "ip",
        "ccq",
        "host",
        "noise",
        "signal",
        "uptime",
        "rx_rate",
        "tx_rate",
        "distancia",
        "count_tx",
        "count_rx",
    ],
}


# ============================================================
# FUNCIÓN DE PRUEBA
# ============================================================

def ejecutar_prueba(nombre, metricas):

    print()
    print("=" * 80)
    print(nombre)
    print("=" * 80)

    print()
    print("OID solicitados:")

    for nombre_metrica in metricas:
        print(
            f"  {nombre_metrica:12} -> {OID[nombre_metrica]}"
        )

    print()
    print("Ejecutando nextCmd()...")
    print()

    # --------------------------------------------------------
    # Construimos los ObjectType
    # --------------------------------------------------------

    objetos_snmp = [
        ObjectType(
            ObjectIdentity(OID[nombre_metrica])
        )
        for nombre_metrica in metricas
    ]

    # --------------------------------------------------------
    # Motor SNMP
    # --------------------------------------------------------

    engine = SnmpEngine()

    community = CommunityData(
        COMMUNITY,
        mpModel=0,       # SNMPv1
    )

    transporte = UdpTransportTarget(
        (IP, PORT),
        timeout=3,
        retries=1,
    )

    contexto = ContextData()

    fila_numero = 0

    # --------------------------------------------------------
    # nextCmd
    # --------------------------------------------------------

    try:

        for (
            errorIndication,
            errorStatus,
            errorIndex,
            varBinds,
        ) in nextCmd(
            engine,
            community,
            transporte,
            contexto,
            *objetos_snmp,
            lexicographicMode=False,
        ):

            fila_numero += 1

            print("-" * 80)
            print(f"FILA {fila_numero}")
            print("-" * 80)

            # ------------------------------------------------
            # Error indication
            # ------------------------------------------------

            if errorIndication:

                print()
                print("ERROR INDICATION")
                print(
                    f"  {errorIndication}"
                )

                break

            # ------------------------------------------------
            # Error status
            # ------------------------------------------------

            elif errorStatus:

                print()
                print("ERROR STATUS")
                print(
                    f"  {errorStatus.prettyPrint()}"
                )

                if errorIndex:

                    print(
                        f"  Error index: {errorIndex}"
                    )

                    if 0 < errorIndex <= len(metricas):

                        print(
                            "  Métrica afectada: "
                            f"{metricas[errorIndex - 1]}"
                        )

                break

            # ------------------------------------------------
            # Respuesta
            # ------------------------------------------------

            else:

                for posicion, varBind in enumerate(varBinds):

                    oid_respuesta, valor = varBind

                    print()

                    print(
                        f"[{posicion}] "
                        f"Métrica solicitada: "
                        f"{metricas[posicion]}"
                    )

                    print(
                        f"    OID respuesta : "
                        f"{oid_respuesta.prettyPrint()}"
                    )

                    print(
                        f"    Valor         : "
                        f"{valor.prettyPrint()}"
                    )

                    print(
                        f"    Tipo          : "
                        f"{type(valor)}"
                    )

                    # ----------------------------------------
                    # Comprobación específica Counter64
                    # ----------------------------------------

                    if metricas[posicion] in (
                        "count_tx",
                        "count_rx",
                    ):

                        try:

                            valor_int = int(valor)

                            print(
                                f"    int(valor)    : "
                                f"{valor_int}"
                            )

                        except Exception as exc:

                            print(
                                "    ERROR convirtiendo "
                                f"Counter64 a int: {exc}"
                            )

    except Exception as exc:

        print()
        print("=" * 80)
        print("EXCEPCIÓN PYTHON")
        print("=" * 80)

        print(
            f"{type(exc).__name__}: {exc}"
        )

    print()
    print("=" * 80)
    print(f"FIN: {nombre}")
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("TEST SNMP UBIQUITI - PySNMP / SNMPv1")
    print("=" * 80)

    print()
    print(f"Dispositivo : {IP}")
    print(f"Comunidad   : {COMMUNITY}")
    print(f"Puerto      : {PORT}")
    print("Protocolo   : SNMPv1")
    print()

    for nombre_prueba, metricas in PRUEBAS.items():

        ejecutar_prueba(
            nombre_prueba,
            metricas,
        )

        input(
            "\nPulsa ENTER para continuar con la siguiente prueba..."
        )


if __name__ == "__main__":
    main()
