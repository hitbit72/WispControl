"""
Servicio para envío de notificaciones por Telegram.
"""
import logging
import threading
import requests

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


def _build_message(dispositivo, alarma, accion):
    """
    Construye el mensaje de Telegram.
    
    Args:
        dispositivo: Instancia de Dispositivo
        alarma: Instancia de Alarma
        accion: 'nueva' o 'resuelta'
    
    Returns:
        str: Mensaje formateado para Telegram
    """
    emoji = {
        'nueva': '🚨',
        'resuelta': '✅',
    }.get(accion, '📢')
    
    tipo_emoji = {
        'snmp': '📡',
        'ping': '🏓',
        'mkt': '🔧',
    }.get(alarma.tipo, '⚠️')
    
    """
    lines = [
        f"{emoji} <b>{alarma.titulo}</b>",
        f"{tipo_emoji} <b>Dispositivo:</b> {dispositivo.nombre} ({dispositivo.ip_gestion})",
        f"📋 <b>Regla:</b> {alarma.regla}",
        f"📝 <b>Detalle:</b> {alarma.texto or '—'}",
    ]
    """
    if accion == 'resuelta' and alarma.resuelta_en:
        detec = f"⏱ <b>Resuelta:</b> {alarma.resuelta_en.strftime('%d/%m/%Y %H:%M:%S')}"
    elif accion == 'nueva':
        detec = f"🕐 <b>Detectada:</b> {alarma.creada_en.strftime('%d/%m/%Y %H:%M:%S')}"

    lines = [
        f"{emoji} <b>{alarma.titulo}</b>",
        detec,
        f"<b>{dispositivo.nombre}</b> ({dispositivo.ip_gestion})",
        f"{alarma.texto or '—'}",
    ]

    """
    if accion == 'resuelta' and alarma.resuelta_en:
        lines.append(f"⏱ <b>Resuelta:</b> {alarma.resuelta_en.strftime('%d/%m/%Y %H:%M:%S')}")
    elif accion == 'nueva':
        lines.append(f"🕐 <b>Detectada:</b> {alarma.creada_en.strftime('%d/%m/%Y %H:%M:%S')}")
    """

    # Estado actual del dispositivo
    #estado_label = dict(dispositivo.Estado.choices).get(dispositivo.estado, dispositivo.estado)
    #lines.append(f"🔘 <b>Estado:</b> {estado_label}")
    
    # Métricas relevantes según tipo
    metrica = dispositivo.metricas.first()
    if metrica:
        if alarma.tipo == 'snmp':
            if metrica.signal is not None:
                lines.append(f"📶 Señal: {metrica.signal} dBm")
            if metrica.frequency is not None:
                lines.append(f"📶 Frecuencia: {metrica.frequency} Mhz")
        elif alarma.tipo == 'ping':
            if metrica.latencia is not None:
                lines.append(f"⏱ Latencia: {metrica.latencia} ms")
    """
    if metrica:
        if alarma.tipo == 'snmp':
            if metrica.cpu is not None:
                lines.append(f"💻 CPU: {metrica.cpu:.0f}%")
            if metrica.ram is not None:
                lines.append(f"🧠 RAM: {metrica.ram:.0f}%")
            if metrica.signal is not None:
                lines.append(f"📶 Señal: {metrica.signal} dBm")
            if metrica.frequency is not None:
                lines.append(f"📶 Frecuencia: {metrica.frequency} Mhz")
        elif alarma.tipo == 'ping':
            if metrica.latencia is not None:
                lines.append(f"⏱ Latencia: {metrica.latencia} ms")
    """

    # Sector si existe
    if dispositivo.sector:
        # lines.append(f"📍 Sector: {dispositivo.sector.nombre}")
        lines.append(f"Sector: {dispositivo.sector.nombre}")
    
    return "\n".join(lines)


def _send_telegram_sync(message):
    """
    Envía mensaje a Telegram de forma síncrona.
    
    Returns:
        bool: True si se envió correctamente
    """
    bot_id = getattr(settings, 'TELEGRAM', {}).get('BOTID', '')
    chat_id = getattr(settings, 'TELEGRAM', {}).get('CHATID', '')
    timeout = getattr(settings, 'TELEGRAM', {}).get('TIMEOUT', 10)
    sound = getattr(settings, 'TELEGRAM', {}).get('SOUND', 0)
    
    if not bot_id or not chat_id:
        logger.warning("Telegram no configurado: faltan BOTID o CHATID en settings")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Telegram no configurado: faltan BOTID o CHATID en settings")
        return False
    
    url = f"{getattr(settings, 'TELEGRAM', {}).get('URL', 'https://api.telegram.org/')}bot{bot_id}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_notification': sound == 0,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if result.get('ok'):
            logger.info(f"Telegram enviado: message_id={result['result']['message_id']}")
            #print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Telegram enviado: message_id={result['result']['message_id']}")
            return True
        else:
            logger.error(f"Error Telegram API: {result}")
            print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Error Telegram API: {result}")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout enviando a Telegram ({timeout}s)")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Timeout enviando a Telegram ({timeout}s)")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red enviando a Telegram: {e}")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Error de red enviando a Telegram: {e}")
        return False
    except Exception as e:
        logger.exception(f"Error inesperado enviando a Telegram: {e}")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Error inesperado enviando a Telegram: {e}")
        return False


def enviar_alerta_telegram(dispositivo, alarma, accion):
    """
    Envía alerta por Telegram en un hilo separado (no bloqueante).
    
    Args:
        dispositivo: Instancia de Dispositivo
        alarma: Instancia de Alarma
        accion: 'nueva' o 'resuelta'
    
    Returns:
        threading.Thread: El hilo creado (para posible join si se necesita)
    """
    # Verificar si el dispositivo tiene notificaciones habilitadas
    if alarma.tipo == 'snmp' and not dispositivo.alarma:
        logger.debug(f"Dispositivo {dispositivo.nombre} tiene alarma=False, omitiendo Telegram")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Dispositivo {dispositivo.nombre} tiene alarma=False, omitiendo Telegram")
        return None
    if alarma.tipo == 'ping' and not dispositivo.alarma_ping:
        logger.debug(f"Dispositivo {dispositivo.nombre} tiene alarma_ping=False, omitiendo Telegram")
        print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Dispositivo {dispositivo.nombre} tiene alarma_ping=False, omitiendo Telegram")
        return None
    
    message = _build_message(dispositivo, alarma, accion)
    
    def _worker():
        try:
            _send_telegram_sync(message)
        except Exception as e:
            logger.exception(f"Error en hilo Telegram: {e}")
            print(f"[{timezone.now():%d/%m/%Y %H:%M:%S}] Error en hilo Telegram: {e}")
    
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def enviar_alerta_telegram_sync(dispositivo, alarma, accion):
    """
    Versión síncrona para testing o uso directo.
    
    Returns:
        bool: True si se envió correctamente
    """
    if alarma.tipo == 'snmp' and not dispositivo.alarma:
        return False
    if alarma.tipo == 'ping' and not dispositivo.alarma_ping:
        return False
    
    message = _build_message(dispositivo, alarma, accion)
    return _send_telegram_sync(message)