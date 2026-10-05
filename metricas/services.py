"""
Servicio del módulo metricas: guarda la métrica capturada, sincroniza las
alarmas con las reglas detectadas y actualiza el estado del dispositivo.
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from eventos.models import Evento
from eventos.services import registrar_evento

from dispositivos.models import Dispositivo, Interfaz, dispositivos_ap

from .models import Alarma, DeviceMetrics, DeviceMetricHistory, InterfaceMetricHistory
from .reglas import REGLA_NIVEL, evaluar
from telegram.services import enviar_alerta_telegram

MODULO = 'metricas'


def guardar_metrica(dispositivo, **datos):
    """ Crea la fila DeviceMetrics.
        Se actualiza siempre el mismo registro, ya que se refiere siempre al
        mismo dispositivo y no necesitamos datos a lo largo del tiempo.
        Usamos timescan solo para saber cuando se actualizó.
    """
    metricas = DeviceMetrics.objects.update_or_create(
        device=dispositivo,
        defaults=datos
    )[0]


    # Lista de campos relevantes para el histórico, para evitar guardar metricas vacias
    campos_historico = [
        'cpu', 'ram', 'temperature', 'ccq', 'power', 
        'signal', 'noise', 'tx', 'rx'
    ]
    # Comprobamos si al menos una métrica viene en 'datos' con un valor distinto de None
    tiene_datos = any(datos.get(campo) is not None for campo in campos_historico)

    if tiene_datos:
        # Guardamos el hístórico general
        historico = DeviceMetricHistory.objects.create(
            device = dispositivo,
            timestamp = timezone.now(),
            cpu = datos.get('cpu', 0),
            ram = datos.get('ram', 0),
            temperature = datos.get('temperature', 0),
            ccq = datos.get('ccq', 0),
            power = datos.get('power', 0),
            signal = datos.get('signal', 0),
            noise = datos.get('noise',0 ),
            tx_capacity  = datos.get('tx', 0),
            rx_capacity = datos.get('rx', 0),
        )
    else:
        historico = None

    return metricas, historico




def guardar_puertos(dispositivo, **datos):
    """
    Guarda o actualiza las interfaces/puertos recibidos en el diccionario de métricas.
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

        #if not puerto["speed"]:
        if puerto["estado"] == 'down':
            uData = {
                "estado": puerto["estado"],
            }

        # Tipo de interface según su nombre (802.1Q=trunk VLAN)
        if any(exclude.lower() in puerto['nombre'].lower() for exclude in ('ath', 'wifi', 'wlan')):
            uData.update({'tipo': Interfaz.Tipo.WIRELESS})
        elif any(exclude.lower() in puerto['nombre'].lower() for exclude in ('eth', 'br')):
            uData.update({'tipo': Interfaz.Tipo.ETHERNET})
        elif any(exclude.lower() in puerto['nombre'].lower() for exclude in ('ppp',)):
            uData.update({'tipo': Interfaz.Tipo.PPPOE})

        # Actualizamos o registramos el puero si no existe
        interfaz, created = Interfaz.objects.update_or_create(
            dispositivo=dispositivo,
            nombre=puerto["nombre"],
            defaults=uData,
        )

        # guardamos las metrcias históricas solo de dispositivos MAIN
        #if dispositivo.rol == Dispositivo.Rol.MAIN:
        
        if interfaz:
            if puerto["estado"] == 'up':
                InterfaceMetricHistory.objects.create(
                    interfaz = interfaz,
                    timestamp = timezone.now(),
                    rx = puerto["rx_counter"],
                    tx = puerto["tx_counter"],
                )



    # Puertos especiales de la olt ubiquiti
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
            # Actualizamos o registramos el puero si no existe
            interfaz, created = Interfaz.objects.update_or_create(
                dispositivo=dispositivo,
                nombre=puerto["nombre"],
                defaults=uData,
            )





def guarda_staciones_wifi(dispositivo, **datos):
    """ 
    Guarda los datos básicos de los dispositivos 'Antena de cliente'.
    Pone en activo la estación
    """
    # Extraer la lista de estaciones del diccionario (si no existe, usa lista vacía)
    estaciones = datos.get("estaciones", [])
    ssid = datos.get('ssid')
    frequency = datos.get('frequency')

    ultima_ip = ''
    for estacion in estaciones:
        # buscamos la IP de la estación
        ip = estacion.get('ip')
        if not ip:
            continue

        # Evitar duplicados en estaciones
        if ultima_ip == ip:
            ultima_ip = ''
            continue

        ultima_ip = ip

        # Obtenemos la INSTANCIA única del dispositivo por su IP de gestión
        estacion_dev = Dispositivo.objects.filter(ip_gestion=ip).first()

        # Actualización de datos. Se tiene que usar las keys de OID
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

        # Guardamos la metrica estática
        if estacion_dev:
            st, created = DeviceMetrics.objects.update_or_create(
                device=estacion_dev,
                defaults=uData,
            )

            # -------- METRICA DE LA ESTACIÓN PROPORCIONADA POR EL AP
            # Guardamos esta métrica porque se proporciona con Counter64, más fiable
            
            if dispositivo.rol != Dispositivo.Rol.MAIN:
                continue

            interfaz = Interfaz.objects.filter(
                dispositivo=estacion_dev
                ).filter(nombre='Wifi-AP').first()

            if not interfaz:
                # Creamos la interfaz Enlace-ap de las estacion
                interfaz, created = Interfaz.objects.update_or_create(
                    dispositivo=estacion_dev,
                    nombre='Wifi-AP',
                    tipo=Interfaz.Tipo.WIRELESS,
                    estado=Interfaz.Estado.ARRIBA,
                    descripcion='Enlace con AP',
                )

            if interfaz:
                # guardamos las metrcias históricas
                InterfaceMetricHistory.objects.create(
                    interfaz = interfaz,
                    timestamp = timezone.now(),
                    rx = estacion.get('rx_counter'),
                    tx = estacion.get('tx_counter'),
                )


        # Si el dispositivo no existe, se puede crear cómo Discover. (Queda pendiente)



def guarda_estaciones_onu(dispositivo, **datos):
    """ 
        Guarda los datos básicos de los dispositivos 'onu' de ubiquiti.
        Estos dispositivos no tiene servicio SNMP.

    """

    # Extraer la lista de estaciones del diccionario (si no existe, usa lista vacía)
    onus = datos.get("onus", [])
    ssid = datos.get('sys_name')

    for onu in onus:
        # buscamos el serial de al ONU, ya que no disponemos de la IP
        serial = onu.get('serial')
        if not serial:
            continue

        # Se tiene que relacionar las keys de OID con el modelo.
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
        

def evaluar_y_aplicar(dispositivo, metrica, anterior, historico, historico_anterior):
    """Evalúa las reglas sobre la métrica recién creada y aplica alarmas y
    estado. Devuelve dict {nuevas, resueltas} con las alarmas tocadas."""

    resultados =[]

    activas = evaluar(dispositivo, metrica, anterior, historico, historico_anterior, settings.METRICAS_ALARMAS)
    if dispositivo.alarma:
        resultados = _sincronizar_alarmas(dispositivo, activas)
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
        #print(f'{regla} - {pk}')
        if regla in detectadas:
            #print('regla sigue activa')
            continue
        
        alarma = Alarma.objects.get(pk=pk)
        alarma.estado = Alarma.Estado.RESUELTA
        alarma.resuelta_en = timezone.now()
        alarma.nivel = Alarma.Nivel.NOTICE,
        alarma.save(update_fields=['estado', 'resuelta_en'])
        registrar_evento(
            MODULO,
            f'Alarma resuelta: {alarma.titulo}',
            f'{alarma.texto}',
            nivel=Evento.Nivel.NOTICE,
            id_dispositivo=dispositivo.pk,
        )
        # Enviar Telegram (async)
        enviar_alerta_telegram(dispositivo, alarma, 'resuelta')
        resultados['resueltas'].append(alarma)

    for regla, datos in detectadas.items():
        if regla in reglas_activas:
            continue

        nivel=REGLA_NIVEL.get(regla, Alarma.Nivel.WARNING)
        alarma, creada = Alarma.objects.get_or_create(
            device=dispositivo,
            regla=regla,
            tipo=Alarma.Tipo.SNMP,
            estado=Alarma.Estado.ACTIVA,
            nivel=nivel,
            defaults={'titulo': datos['titulo'], 'texto': datos['texto']},
        )
        if not creada:
            continue
        
        registrar_evento(
            MODULO, alarma.titulo,
            f'{alarma.texto}',
            nivel=nivel,
            id_dispositivo=dispositivo.pk,
        )
        # Enviar Telegram (async)
        enviar_alerta_telegram(dispositivo, alarma, 'nueva')
        resultados['nuevas'].append(alarma)
    return resultados
