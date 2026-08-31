"""
Servicios para el control de ping a dispositivos.
"""
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from dispositivos.models import Dispositivo
from metricas.models import DeviceMetrics, Alarma
from eventos.services import registrar_evento
from eventos.models import Evento

try:
    from pythonping import ping
except ImportError:
    ping = None


MODULO = 'pingcontrol'

# Configuración por defecto
DEFAULT_PING_CONFIG = {
    'count': 3,
    'timeout': 2,
    'interval': 0.2,
}

def get_ping_config():
    """Obtiene la configuración de ping desde settings o usa defaults."""
    return getattr(settings, 'PING_CONTROL', DEFAULT_PING_CONFIG)


def ping_dispositivo(dispositivo):
    """
    Hace ping a un dispositivo y devuelve (exitoso, latencia_promedio_ms, error_msg).
    
    Returns:
        tuple: (bool, float|None, str|None)
            - bool: True si al menos un ping tuvo respuesta
            - float: latencia promedio en ms (None si falló)
            - str: mensaje de error (None si éxito)
    """
    if ping is None:
        return False, None, "pythonping no está instalado"

    """
    if dispositivo.ip_gestion:
        ip_dispositivo = dispositivo.ip_gestion
    elif dispositivo.ip_publica:
        ip_dispositivo = dispositivo.ip_publica
    else:
        return False, None, "Sin IP de gestión"
    """

    if not dispositivo.ip_gestion:
        return False, None, "Sin IP de gestión"
    
    config = get_ping_config()
    count = config.get('count', DEFAULT_PING_CONFIG['count'])
    timeout = config.get('timeout', DEFAULT_PING_CONFIG['timeout'])
    interval = config.get('interval', DEFAULT_PING_CONFIG['interval'])
    print(f'Ping a {dispositivo.ip_gestion}')

    try:
        result = ping(
            str(dispositivo.ip_gestion),
            count=count,
            timeout=timeout,
            interval=interval,
        )
        
        if result.success():
            # Calcular latencia promedio de los pings exitosos en ms
            latencias = [r.time_elapsed_ms for r in result if r.success]
            if latencias:
                latencia_promedio = sum(latencias) / len(latencias)
                return True, round(latencia_promedio, 2), None
            return True, 0.0, None
        else:
            return False, None, f"Sin respuesta tras {count} pings"
            
    except Exception as e:
        return False, None, f"Error en ping: {str(e)}"


def guardar_metrica_ping(dispositivo, exitoso, latencia, error_msg=None):
    """
    Guarda o actualiza la métrica de ping en DeviceMetrics.
    """
    from metricas.services import guardar_metrica
    
    datos = {
        'status_ping': DeviceMetrics.Status.OK if exitoso else DeviceMetrics.Status.TIMEOUT,
        'latencia': latencia,
        'timeping': timezone.now(),
    }
    
    #if error_msg:
    #    datos['sys_descr'] = error_msg
    
    return guardar_metrica(dispositivo, **datos)


def evaluar_ping(dispositivo, metrica, anterior):
    """
    Evalúa el resultado del ping y genera alarmas si corresponde.
    Retorna lista de alarmas detectadas.
    """
    reglas = []
    
    # Regla: sin respuesta a ping
    if metrica.status_ping != DeviceMetrics.Status.OK:
        texto = f'{dispositivo.ip_gestion} ({dispositivo.nombre}) no responde a ping.'
        if metrica.sys_name:
            texto += f' ({metrica.sys_name})'
        reglas.append({
            'regla': 'ping_sin_respuesta',
            'titulo': f'Ping sin respuesta {dispositivo.ip_gestion}',
            'texto': texto,
        })
    
    # Regla: recuperado (estaba inactivo y ahora responde)
    elif anterior and anterior.status_ping != DeviceMetrics.Status.OK:
        reglas.append({
            'regla': 'ping_recuperado',
            'titulo': f'Ping recuperado {dispositivo.ip_gestion}',
            'texto': f'{dispositivo.ip_gestion} ({dispositivo.nombre}) vuelve a responder a ping (latencia: {metrica.latencia} ms).',
        })
    
    return reglas


def sincronizar_alarmas_ping(dispositivo, detectadas, error_msg):
    """
    Sincroniza alarmas de ping: crea nuevas, resuelve las que ya no aplican.
    regla='ping_sin_respuesta'
    """

    activas = Alarma.objects.filter(
        device=dispositivo, 
        tipo=Alarma.Tipo.PING,
        estado=Alarma.Estado.ACTIVA)
    reglas_activas = dict(activas.values_list('regla', 'pk'))
    detectadas_dict = {a['regla']: a for a in detectadas}
    
    resultados = {'nuevas': [], 'resueltas': []}
    
    # Resolver alarmas que ya no se cumplen
    for regla, pk in reglas_activas.items():
        if regla in detectadas_dict:
            continue
        if regla not in ('ping_sin_respuesta', 'ping_recuperado'):
            continue
            
        alarma = Alarma.objects.get(pk=pk)
        alarma.estado = Alarma.Estado.RESUELTA
        alarma.resuelta_en = timezone.now()
        alarma.save(update_fields=['estado', 'resuelta_en'])

        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                f'Alarma resuelta: {alarma.titulo}',
                f'{dispositivo.nombre} · {alarma.texto}',
                nivel=Evento.Nivel.NOTICE,
            )
        resultados['resueltas'].append(alarma)
    
    # Crear nuevas alarmas
    for regla, datos in detectadas_dict.items():
        if regla not in ('ping_sin_respuesta', 'ping_recuperado'):
            continue
            
        if regla in reglas_activas:
            continue
            
        # Determinar nivel según la regla
        nivel = Evento.Nivel.CRITICAL if regla == 'ping_sin_respuesta' else Evento.Nivel.NOTICE
        
        alarma, creada = Alarma.objects.get_or_create(
            device=dispositivo,
            regla=regla,
            estado=Alarma.Estado.ACTIVA,
            tipo=Alarma.Tipo.PING,
            sys_error=error_msg,
            defaults={'titulo': datos['titulo'], 'texto': datos['texto']},
        )
        
        if not creada:
            continue

        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                alarma.titulo,
                f'{dispositivo.nombre} · {alarma.texto}',
                nivel=nivel,
            )
        resultados['nuevas'].append(alarma)
    
    return resultados


def actualizar_estado_dispositivo(dispositivo, detectadas):
    """
    Actualiza el estado del dispositivo según las alarmas de ping.
    Solo toca estados 'activo'/'inactivo'.
    """
    if dispositivo.estado not in (Dispositivo.Estado.ACTIVO, Dispositivo.Estado.INACTIVO):
        return
    
    # Verificar si hay alarma de ping sin respuesta activa
    ping_caido = any(a['regla'] == 'ping_sin_respuesta' for a in detectadas)
    #ping_recuperado = any(a['regla'] == 'ping_recuperado' for a in detectadas)
    
    if ping_caido and dispositivo.estado == Dispositivo.Estado.ACTIVO:
        dispositivo.estado = Dispositivo.Estado.INACTIVO
        dispositivo.save(update_fields=['estado'])

        """
        ya se genera un aviso en sincronizar_alarmas_ping

        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                f'Dispositivo inactivo por ping: {dispositivo.ip_gestion}',
                f'{dispositivo.nombre} marcado como inactivo por no responder a ping.',
                nivel=Evento.Nivel.NOTICE,
            )
        """
    
    elif not ping_caido and dispositivo.estado == Dispositivo.Estado.INACTIVO:
        dispositivo.estado = Dispositivo.Estado.ACTIVO
        dispositivo.save(update_fields=['estado'])

        """
        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                f'Dispositivo recuperado por ping: {dispositivo.ip_gestion}',
                f'{dispositivo.nombre} vuelve a responder a ping, marcado como activo.',
                nivel=Evento.Nivel.NOTICE,
            )
        """


# Funcion original que no funciona correctamente (desabilitada)
def actualizar_estado_dispositivo_original(dispositivo, detectadas):
    """
    Actualiza el estado del dispositivo según las alarmas de ping.
    Solo toca estados 'activo'/'inactivo'.
    """
    if dispositivo.estado not in (Dispositivo.Estado.ACTIVO, Dispositivo.Estado.INACTIVO):
        return
    
    # Verificar si hay alarma de ping sin respuesta activa
    ping_caido = any(a['regla'] == 'ping_sin_respuesta' for a in detectadas)
    ping_recuperado = any(a['regla'] == 'ping_recuperado' for a in detectadas)
    
    if ping_caido and dispositivo.estado == Dispositivo.Estado.ACTIVO:
        dispositivo.estado = Dispositivo.Estado.INACTIVO
        dispositivo.save(update_fields=['estado'])

        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                f'Dispositivo inactivo por ping: {dispositivo.ip_gestion}',
                f'{dispositivo.nombre} marcado como inactivo por no responder a ping.',
                nivel=Evento.Nivel.CRITICAL,
            )
    
    elif ping_recuperado and dispositivo.estado == Dispositivo.Estado.INACTIVO:
        dispositivo.estado = Dispositivo.Estado.ACTIVO
        dispositivo.save(update_fields=['estado'])

        if dispositivo.alarma_ping:
            registrar_evento(
                MODULO,
                f'Dispositivo recuperado por ping: {dispositivo.ip_gestion}',
                f'{dispositivo.nombre} vuelve a responder a ping, marcado como activo.',
                nivel=Evento.Nivel.NOTICE,
            )


def procesar_dispositivo(dispositivo):
    """
    Procesa un dispositivo: hace ping, guarda métrica, evalúa alarmas, actualiza estado.
    """
    # Hacer ping
    exitoso, latencia, error_msg = ping_dispositivo(dispositivo)
    if error_msg:
        print(error_msg)

    # Guardar métrica
    metrica = guardar_metrica_ping(dispositivo, exitoso, latencia, error_msg)
    
    # Obtener métrica anterior
    anterior = DeviceMetrics.objects.filter(
        device=dispositivo, pk__lt=metrica.pk
    ).order_by('-pk').first()
    
    # Evaluar alarmas de ping
    detectadas = evaluar_ping(dispositivo, metrica, anterior)
    
    # Sincronizar alarmas
    #if dispositivo.alarma_ping:
    sincronizar_alarmas_ping(dispositivo, detectadas, error_msg)
    
    # Actualizar estado del dispositivo
    actualizar_estado_dispositivo(dispositivo, detectadas)
    
    return metrica, detectadas