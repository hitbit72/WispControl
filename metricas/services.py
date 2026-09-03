"""
Servicio del módulo metricas: guarda la métrica capturada, sincroniza las
alarmas con las reglas detectadas y actualiza el estado del dispositivo.
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from eventos.models import Evento
from eventos.services import registrar_evento

from dispositivos.models import Dispositivo, Interfaz

from .models import Alarma, DeviceMetrics
from .reglas import REGLA_INACTIVO, REGLA_NIVEL, evaluar

MODULO = 'metricas'


def guardar_metrica(dispositivo, **datos):
    """ Crea la fila DeviceMetrics.
        Se actualiza siempre el mismo registro, ya que se refiere siempre al
        mismo dispositivo y no necesitamos datos a lo largo del tiempo.
        Usamos timescan y timeping solo para saber cuando se actualizó.
    """
    #datos.setdefault('status', DeviceMetrics.Status.OK)
    #datos.setdefault('timescan', timezone.now())
    #print(f'Datos despues: {datos}')
    return DeviceMetrics.objects.update_or_create(
        device=dispositivo,
        defaults=datos
    )[0]


def guardar_puertos(dispositivo, **datos):
    """Guarda o actualiza las interfaces/puertos recibidos en el diccionario de métricas.
    :param dispositivo: Instancia del modelo Dispositivo (o su objeto/ID)
    :param datos: Diccionario con los datos recopilados por SNMP
    """
    # Extraer la lista de puertos del diccionario (si no existe, usa lista vacía)
    puertos = datos.get("puertos", [])

    for puerto in puertos:
        # update_or_create busca por los kwargs principales (dispositivo + nombre)
        # y actualiza o establece los campos definidos en defaults.
        uData = {
            "estado": puerto["estado"],
            "velocidad_mbps": puerto["speed"],
        }
        if not puerto["speed"]:
            uData = {
                "estado": puerto["estado"],
            }
        #print(f' {puerto["nombre"]}: {uData}')
        interfaz, created = Interfaz.objects.update_or_create(
            dispositivo=dispositivo,
            nombre=puerto["nombre"],
            defaults=uData,
        )

    if datos.get("puertos_pon"):
        puertos = datos.get("puertos", [])
        for puerto in puertos:
            # update_or_create busca por los kwargs principales (dispositivo + nombre)
            # y actualiza o establece los campos definidos en defaults.
            uData = {
                "estado": puerto["estado"],
                "velocidad_mbps": puerto["speed"],
            }
            if not puerto["speed"]:
                uData = {
                    "estado": puerto["estado"],
                }
            #print(f' {puerto["nombre"]}: {uData}')
            interfaz, created = Interfaz.objects.update_or_create(
                dispositivo=dispositivo,
                nombre=puerto["nombre"],
                defaults=uData,
            )

def guarda_staciones_wifi(dispositivo, **datos):
    """ Guarda los datos básicos de los dispositivos 'Antena de cliente' """

    # Extraer la lista de estaciones del diccionario (si no existe, usa lista vacía)
    estaciones = datos.get("estaciones", [])
    ssid = datos.get('ssid')
    frequency = datos.get('frequency')

    for estacion in estaciones:
        # buscamos la IP de la estación
        ip = estacion.get('ip')
        if not ip:
            continue

        # Se tiene que usar las keys de OID
        uData = {
            'ccq': estacion.get('ccq'),
            'noise': estacion.get('noise'),
            'signal': estacion.get('signal'),
            'rx': estacion.get('rx_rate'),
            'tx': estacion.get('tx_rate'),
            'distancia': estacion.get('distancia'),
            'uptime': estacion.get('uptime'),
            'ssid': ssid,
            'frequency': frequency,
        }

        # Obtenemos la INSTANCIA única del dispositivo por su IP de gestión
        # estacion_dev = Dispositivo.objects.filter(ip_gestion=ip).first()

        # Guarda las metricas en cada estacion wifi
        estacion_dev = Dispositivo.objects.filter(
            Q(ip_gestion=ip) | Q(ip_publica=ip)
        ).first()
        
        if estacion_dev:
            st, created = DeviceMetrics.objects.update_or_create(
                device=estacion_dev,
                defaults=uData,
            )


def guarda_estaciones_onu(dispositivo, **datos):
    """ Guarda los datos básicos de los dispositivos 'onu' de ubiquiti """

    # Extraer la lista de estaciones del diccionario (si no existe, usa lista vacía)
    onus = datos.get("onus", [])
    ssid = datos.get('sys_name')

    for onu in onus:
        # buscamos el serial de al ONU, ya que no disponemos de la IP
        serial = onu.get('serial')
        if not serial:
            continue

        # Se tiene que usar las keys de OID
        uData = {
            'signal': onu.get('signal'),
            'power': onu.get('power'),
            'ssid': ssid,
        }

        # Guarda las metricas en cada estacion ONU, los dispotivos Ubiquiti no tienen SNMP
        # Obtenemos la INSTANCIA única del dispositivo por su serial, ya que la OLT no da las IPs
        estacion_dev = Dispositivo.objects.filter(onu_ref=serial).first()
        if estacion_dev:
            st, created = DeviceMetrics.objects.update_or_create(
                device=estacion_dev,
                defaults=uData,
            )
        

def evaluar_y_aplicar(dispositivo, metrica):
    """Evalúa las reglas sobre la métrica recién creada y aplica alarmas y
    estado. Devuelve dict {nuevas, resueltas} con las alarmas tocadas."""
    resultados =[]
    anterior = (
        DeviceMetrics.objects.filter(device=dispositivo, pk__lt=metrica.pk)
        .order_by('-pk').first()
    )
    activas = evaluar(dispositivo, metrica, anterior, settings.METRICAS_ALARMAS)
    if dispositivo.alarma:
        resultados = _sincronizar_alarmas(dispositivo, activas)

    # ATENCION: 
    # _actualizar_estado esta desactivado
    # Activar y desactivar dispositivos lo administra el modulo ping, aquí solo se muetra la alerta
    #_actualizar_estado(dispositivo, activas)  <----

    return resultados


def _sincronizar_alarmas(dispositivo, detectadas):
    """ Alta de las reglas nuevas, resolución de las que ya no se cumplen. regla='sin_respuesta_snmp' """
    
    activas = Alarma.objects.filter(
        device=dispositivo, 
        tipo=Alarma.Tipo.SNMP,
        estado=Alarma.Estado.ACTIVA
    )

    reglas_activas = dict(activas.values_list('regla', 'pk'))
    detectadas = {a['regla']: a for a in detectadas}

    resultados = {'nuevas': [], 'resueltas': []}

    for regla, pk in reglas_activas.items():
        if regla in detectadas:
            continue
        if regla not in REGLA_INACTIVO:
            continue
        alarma = Alarma.objects.get(pk=pk)
        alarma.estado = Alarma.Estado.RESUELTA
        alarma.resuelta_en = timezone.now()
        alarma.save(update_fields=['estado', 'resuelta_en'])
        registrar_evento(
            MODULO,
            f'Alarma resuelta: {alarma.titulo}',
            f'{dispositivo.nombre} · {alarma.texto}',
            nivel=Evento.Nivel.NOTICE,
        )
        resultados['resueltas'].append(alarma)

    for regla, datos in detectadas.items():
        if regla not in REGLA_INACTIVO:
            continue
        if regla in reglas_activas:
            continue
        alarma, creada = Alarma.objects.get_or_create(
            device=dispositivo,
            regla=regla,
            tipo=Alarma.Tipo.SNMP,
            estado=Alarma.Estado.ACTIVA,
            defaults={'titulo': datos['titulo'], 'texto': datos['texto']},
        )
        if not creada:
            continue
        registrar_evento(
            MODULO, alarma.titulo,
            f'{dispositivo.nombre} · {alarma.texto}',
            nivel=REGLA_NIVEL.get(regla, Evento.Nivel.WARNING),
        )
        resultados['nuevas'].append(alarma)
    return resultados


def _actualizar_estado(dispositivo, detectadas):
    """ Pasa a 'inactivo' cuando hay una regla que marca el dispositivo y
    vuelve a 'activo' cuando las reglas se normalizan. Solo se tocan los
    estados operativos 'activo'/'inactivo' (mantenimiento, instalación,
    retirado quedan intactos). """
    if dispositivo.estado not in (Dispositivo.Estado.ACTIVO, Dispositivo.Estado.INACTIVO):
        return
    inactivo = any(a['regla'] in REGLA_INACTIVO for a in detectadas)

    if inactivo and dispositivo.estado == Dispositivo.Estado.ACTIVO:
        dispositivo.estado = Dispositivo.Estado.INACTIVO
        dispositivo.save(update_fields=['estado'])
        if dispositivo.alarma:
            registrar_evento(
                MODULO, f'Dispositivo sin conectividad: {dispositivo.ip_gestion}',
                'Se marcó como inactivo por falta de respuesta SNMP.',
                nivel=Evento.Nivel.CRITICAL,
            )
    elif not inactivo and dispositivo.estado == Dispositivo.Estado.INACTIVO:
        dispositivo.estado = Dispositivo.Estado.ACTIVO
        dispositivo.save(update_fields=['estado'])
        if dispositivo.alarma:
            registrar_evento(
                MODULO, f'Dispositivo recuperado: {dispositivo.ip_gestion}',
                'Vuelve a responder correctamente a SNMP.',
                nivel=Evento.Nivel.NOTICE,
            )