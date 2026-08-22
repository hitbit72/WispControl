"""
Ejecuta contra un router MikroTik real (vía librouteros) lo que indica cada
TareaSincronizacion, siguiendo el proceso descrito en
docs/fase2_mikrotik_proceso.md.

IMPORTANTE: este módulo se escribió con base en la documentación pública de
librouteros y en el proceso ya acordado con el cliente, pero no se ha podido
probar contra un router MikroTik real en este entorno de trabajo. Antes de
dejarlo corriendo contra producción, pruébalo primero contra un router de
pruebas (o al menos un plan/contrato de prueba) y revisa los resultados en
el admin (TareaSincronizacion) y directamente en el router.
"""

from django.conf import settings
from .client import conectar

from eventos.models import Evento
from eventos.services import registrar_evento
MODULO = 'mikrotik'


def procesar_tarea(tarea):
    """Punto de entrada: ejecuta la tarea contra el router correspondiente."""
    if tarea.router is None:
        # eventos: 5=notice
        registrar_evento(
            MODULO,
            'Tarea de sincronización sin router asociado',
            f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}): el plan o el '
            'router pudo haberse eliminado.',
            nivel=Evento.Nivel.NOTICE,
        )
        raise RuntimeError(
            'La tarea no tiene un router asociado (el plan o el router pudo haberse eliminado).'
        )

    with conectar(tarea.router) as api:
        if tarea.conexion == 'pppoe':
            _procesar_pppoe(api, tarea)
        elif tarea.conexion == 'sq':
            _procesar_sq(api, tarea)
        else:
            # eventos: 3=error
            registrar_evento(
                MODULO,
                f'Tipo de conexión no soportado: {tarea.conexion!r}',
                f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}).',
                nivel=Evento.Nivel.ERROR,
            )
            raise RuntimeError(f"Tipo de conexión no soportado: {tarea.conexion!r}")


# --- PPPoE -------------------------------------------------------------

def _procesar_pppoe(api, tarea):
    secrets = api.path('ppp', 'secret')
    contrato = tarea.contrato  # puede ser None si la tarea es una 'baja'

    if tarea.operacion == 'alta':
        if _buscar_por_nombre(secrets, tarea.identificador_mikrotik):
            # eventos: 6=info
            registrar_evento(
                MODULO,
                f'Secret PPPoE ya existía: {tarea.identificador_mikrotik}',
                f'Tarea #{tarea.pk} de alta: no se crea porque ya existe en el router.',
                nivel=Evento.Nivel.INFO,
            )
            return  # ya existe, no se crea de nuevo
        secrets.add(**_datos_secret(contrato))
        return

    if tarea.operacion == 'baja':
        existente = _buscar_por_nombre(secrets, tarea.identificador_mikrotik)
        if existente:
            secrets.remove(existente['.id'])
        _desconectar_pppoe_activo(api, tarea.identificador_mikrotik)
        return

    # modificacion
    nombre_buscar = tarea.identificador_anterior or tarea.identificador_mikrotik
    existente = _buscar_por_nombre(secrets, nombre_buscar)
    if not existente:
        # eventos: 4=warning
        registrar_evento(
            MODULO,
            f'Secret PPPoE no encontrado para modificar: {nombre_buscar}',
            f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}). Revisa manualmente '
            'si hay que darlo de alta.',
            nivel=Evento.Nivel.WARNING,
        )
        raise RuntimeError(
            f"No se encontró el secret '{nombre_buscar}' en el router para modificar. "
            "Revisa manualmente si hay que darlo de alta."
        )
    if contrato is None:
        # eventos: 3=error
        registrar_evento(
            MODULO,
            'Contrato eliminado durante modificación PPPoE',
            f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}): no se puede '
            'completar la modificación.',
            nivel=Evento.Nivel.ERROR,
        )
        raise RuntimeError('El contrato ya no existe; no se puede completar la modificación.')

    datos = _datos_secret(contrato)
    datos['.id'] = existente['.id']
    secrets.update(**datos)
    _desconectar_pppoe_activo(api, contrato.identificador_mikrotik)


def _datos_secret(contrato):
    activo = contrato.estado == contrato.Estado.ACTIVO
    datos = {
        'name': contrato.identificador_mikrotik,
        'password': contrato.pppoe_clave,
        'profile': contrato.plan.nombre if activo else contrato.plan.router.ppp_disable,
        'service': 'pppoe',
        'comment': contrato.cliente.nombre_completo,
    }
    if contrato.ip_asignada:
        datos['remote-address'] = contrato.ip_asignada
    return datos


def _desconectar_pppoe_activo(api, nombre):
    if not nombre:
        return
    activos = api.path('ppp', 'active')
    fila = _buscar_por_nombre(activos, nombre)
    if fila:
        activos.remove(fila['.id'])


# --- Simple Queue --------------------------------------------------------

def _procesar_sq(api, tarea):
    queues = api.path('queue', 'simple')
    address_list = api.path('ip', 'firewall', 'address-list')
    contrato = tarea.contrato

    if tarea.operacion == 'alta':
        if _buscar_por_nombre(queues, tarea.identificador_mikrotik):
            registrar_evento(
                MODULO,
                f'Simple Queue ya existía: {tarea.identificador_mikrotik}',
                f'Tarea #{tarea.pk} de alta: no se crea porque ya existe en el router.',
                nivel=Evento.Nivel.INFO,
            )
            return
        queues.add(**_datos_simple_queue(contrato))
        _asegurar_en_active_list(address_list, contrato, activo=True)
        return

    if tarea.operacion == 'baja':
        existente = _buscar_por_nombre(queues, tarea.identificador_mikrotik)
        if existente:
            queues.remove(existente['.id'])
        entrada = _buscar_entrada_lista(address_list, tarea.identificador_mikrotik)
        if entrada:
            address_list.remove(entrada['.id'])
        return

    # modificacion
    nombre_buscar = tarea.identificador_anterior or tarea.identificador_mikrotik
    existente = _buscar_por_nombre(queues, nombre_buscar)
    if not existente:
        # eventos: 4=warning
        registrar_evento(
            MODULO,
            f'Simple Queue no encontrada para modificar: {nombre_buscar}',
            f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}). Revisa manualmente '
            'si hay que darla de alta.',
            nivel=Evento.Nivel.WARNING,
        )
        raise RuntimeError(
            f"No se encontró el queue '{nombre_buscar}' en el router para modificar. "
            "Revisa manualmente si hay que darlo de alta."
        )
    if contrato is None:
        # eventos: 3=error
        registrar_evento(
            MODULO,
            'Contrato eliminado durante modificación de Simple Queue',
            f'Tarea #{tarea.pk} ({tarea.identificador_mikrotik}): no se puede '
            'completar la modificación.',
            nivel=Evento.Nivel.ERROR,
        )
        raise RuntimeError('El contrato ya no existe; no se puede completar la modificación.')

    activo = contrato.estado == contrato.Estado.ACTIVO
    if activo:
        datos = _datos_simple_queue(contrato, incluir_place_before=False)
        datos['.id'] = existente['.id']
        datos['disabled'] = 'no'
        queues.update(**datos)
        _asegurar_en_active_list(address_list, contrato, activo=True)
    else:
        queues.update(**{'.id': existente['.id'], 'disabled': 'yes'})
        _asegurar_en_active_list(address_list, contrato, activo=False)


def _datos_simple_queue(contrato, incluir_place_before=True):
    plan = contrato.plan
    opciones = settings.MK_OPTIONS
    datos = {
        'name': contrato.identificador_mikrotik,
        'target': contrato.ip_asignada,
        'parent': plan.parent,
        'max-limit': f'{plan.velocidad_subida}M/{plan.velocidad_bajada}M',
        'limit-at': f'{plan.limit_up}M/{plan.limit_down}M',
        'priority': f'{plan.priority_up}/{plan.priority_down}',
        'burst-limit': opciones['BURST_LIMIT'],
        'burst-threshold': opciones['BURST_THRESHOLD'],
        'burst-time': opciones['BURST_TIME'],
        'bucket-size': opciones['BUCKET_SIZE'],
        'queue': opciones['QUEUE_TYPE'],
        'total-queue': opciones['TOTAL_QUEUE'],
        'comment': contrato.cliente.nombre_completo,
    }
    if incluir_place_before:
        datos['place-before'] = plan.before
    return datos


def _buscar_entrada_lista(path, identificador):
    """
    Busca en la address-list por 'comment', no por IP: al encolar la baja
    ya no tenemos el contrato (y por tanto tampoco su IP actual), así que
    el identificador guardado como comentario es el único dato estable
    para encontrar la entrada correcta.
    """
    if not identificador:
        return None
    for fila in path:
        if fila.get('comment') == identificador:
            return fila
    return None


def _asegurar_en_active_list(path, contrato, activo):
    router = contrato.plan.router
    existente = _buscar_entrada_lista(path, contrato.identificador_mikrotik)
    datos = {
        'address': contrato.ip_asignada,
        'list': router.active_list,
        'comment': contrato.identificador_mikrotik,
        'disabled': 'no' if activo else 'yes',
    }
    if existente:
        datos['.id'] = existente['.id']
        path.update(**datos)
    else:
        path.add(**datos)


# --- Utilidad compartida --------------------------------------------------

def _buscar_por_nombre(path, nombre):
    """Busca una fila por 'name' en un Path de librouteros. Devuelve el
    diccionario completo (incluye '.id') o None si no existe."""
    if not nombre:
        return None
    for fila in path:
        if fila.get('name') == nombre:
            return fila
    return None
