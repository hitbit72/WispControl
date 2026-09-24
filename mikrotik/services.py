"""
Funciones auxiliares para encolar tareas de sincronización con MikroTik.

Importante: nada de este módulo habla con el router directamente. Solo deja
constancia en TareaSincronizacion para que el servicio MikroTik (proceso
Python aparte) la procese más adelante. Ver docs/fase2_mikrotik_proceso.md.
"""

import unicodedata
from .models import TareaSincronizacion

# Por ahora solo estos tipos de conexión requieren sincronizar con el router.
# PPPoE y SimpleQueue
CONEXIONES_SINCRONIZABLES = ('pppoe', 'sq', 'dhcp')


def quitar_tildes(texto):
    if isinstance(texto, str):
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
    return texto

def encolar_tarea(contrato, operacion, identificador_anterior='', vincular_contrato=True):
    """
    Crea una fila en TareaSincronizacion para que el servicio MikroTik la
    procese. No hace nada (devuelve None) si el contrato no es de un tipo
    de conexión gestionado en el router, o si no tiene identificador
    (no habría nada que buscar/crear en el equipo).

    'vincular_contrato=False' se usa cuando el contrato ya se eliminó de la
    base de datos (baja por borrado real): en ese caso no se puede apuntar
    el FK a una fila que ya no existe, así que la tarea queda sin vínculo
    pero conserva el identificador y el tipo de conexión como copia.
    """
    if contrato.conexion not in CONEXIONES_SINCRONIZABLES:
        return None
    if not contrato.identificador_mikrotik:
        return None

    return TareaSincronizacion.objects.create(
        contrato=contrato if vincular_contrato else None,
        router=contrato.plan.router,
        cliente_nombre=quitar_tildes(contrato.cliente.nombre_completo),
        identificador_mikrotik=contrato.identificador_mikrotik,
        conexion=contrato.conexion,
        plan_nombre=contrato.plan.nombre,
        estado_contrato=contrato.estado,
        operacion=operacion,
        identificador_anterior=identificador_anterior,
    )
