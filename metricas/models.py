from django.db import models


class DeviceMetrics(models.Model):
    """
    Muestra (SNMP) de un dispositivo en un instante concreto.
    Solo la escribe el servicio de monitorización (`manage.py monitorizar`),
    nunca un humano. Cada dispositivo a monitorizar tiene un unico registro
    que se actualiza periodicamente.

    Los campos que no aplican a un dispositivo (o que no soporta por SNMP)
    quedan en NULL / sin valor.
    """

    class Status(models.TextChoices):
        OK = 'ok', 'OK'
        TIMEOUT = 'timeout', 'Sin respuesta'
        ERROR = 'error', 'Error de consulta'

    device = models.ForeignKey('dispositivos.Dispositivo', on_delete=models.CASCADE, related_name='metricas',)

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    timescan = models.DateTimeField(null=True, blank=True, verbose_name='Fecha escaneo SNMP')

    sys_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Nombre sistema')
    sys_descr = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripción')
    version = models.CharField(max_length=255, null=True, blank=True, verbose_name='Versión')

    cpu = models.FloatField(null=True, blank=True, verbose_name='CPU (%)')
    ram = models.FloatField(null=True, blank=True, verbose_name='RAM (%)')
    temperature = models.FloatField(null=True, blank=True, verbose_name='Temperatura (°C)')
    power = models.FloatField(null=True, blank=True, verbose_name='Potencia (W)')
    rx = models.BigIntegerField(null=True, blank=True, verbose_name='Capacidad Rx (bps)')
    tx = models.BigIntegerField(null=True, blank=True, verbose_name='Capacidad Tx (bps)')
    #snr = models.FloatField(null=True, blank=True, verbose_name='SNR (dB)')  # (SNR = Señal - Ruido)
    ccq = models.FloatField(null=True, blank=True, verbose_name='CCQ (%)')
    signal = models.FloatField(null=True, blank=True, verbose_name='Señal (dBm)')
    noise = models.FloatField(null=True,blank=True, verbose_name='Noise floor')

    ssid = models.CharField(max_length=200, null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True, verbose_name='Frecuencia (MHz)')
    w_channel = models.FloatField(null=True,blank=True, verbose_name='Ancho canal')
    antena = models.CharField(max_length=100, null=True, blank=True, verbose_name='Tipo Antena')
    distancia = models.PositiveIntegerField(null=True, blank=True, verbose_name='Distnacia')
    clients = models.PositiveIntegerField(null=True, blank=True, verbose_name='Clientes conectados')
    uptime = models.PositiveBigIntegerField(
        null=True, blank=True,
        verbose_name='Uptime (segundos)',
        help_text='Segundos desde el último reinicio.',
    )

    puertos = models.JSONField(
        default=list, blank=True,
        verbose_name='Interfaces',
        help_text='JSON de interfaz: {speed, estado, nombre, rx_counter, tx_counter}',
    )
    puertos_pon = models.JSONField(
        default=list, blank=True, null=True,
        verbose_name='Puertos PON',
        help_text='JSON de interfaces PON: {speed, estado, nombre, rx_counter, tx_counter}',
    )
    estaciones = models.JSONField(
        default=list, blank=True, null=True,
        verbose_name='Estaciones',
        help_text='JSON de estaciones: {ip, host, noise, signal, uptime, rx_rate, tx_rate, distancia}',
    )
    onus = models.JSONField(
        default=list, blank=True, null=True,
        verbose_name='Onus',
        help_text='JSON de ONUs: {pon, name, model, power, serial, signal}',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OK, verbose_name='Estado SNMP',)

    class Meta:
        verbose_name = 'Métrica de dispositivo'
        verbose_name_plural = 'Métricas de dispositivos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp'], name='device_metrica_idx'),
        ]

    def __str__(self):
        return f'{self.device.nombre} · {self.timestamp:%d/%m/%Y %H:%M} · {self.status}'


# Histórico de latencia de dispositivos
class DeviceLatencyHistory(models.Model):
    device = models.ForeignKey(
        'dispositivos.Dispositivo',
        on_delete=models.CASCADE,
        related_name='latencias',
    )

    timestamp = models.DateTimeField()
    latency_ms = models.FloatField(null=True, blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Histórico de latencia de dispositivo'
        verbose_name_plural = 'Históricos de latencias de dispositivos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]



# Histórico de rx/tx de los puertos
class InterfaceMetricHistory(models.Model):
    interfaz = models.ForeignKey(
        'dispositivos.Interfaz',
        on_delete=models.CASCADE,
        related_name='metricas_historicas',
    )

    timestamp = models.DateTimeField()
    rx = models.BigIntegerField(null=True, blank=True)
    tx = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Histórico de tráfico de interfaz'
        verbose_name_plural = 'Históricos de tráfico de interfaces'
        ordering = ['-timestamp']
        
        constraints = [
            models.UniqueConstraint(
                fields=['interfaz', 'timestamp'],
                name='interface_metric_unique_timestamp',
            ),
        ]
        indexes = [
            models.Index(
                fields=['interfaz', 'timestamp'],
                name='interface_metric_history_idx',
            ),
        ]


# Histótico general de dispositivos
class DeviceMetricHistory(models.Model):
    device = models.ForeignKey(
        'dispositivos.Dispositivo',
        on_delete=models.CASCADE,
        related_name='metrica_historica',
    )

    timestamp = models.DateTimeField()

    # General
    cpu = models.FloatField(null=True, blank=True)
    ram = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)

    # Antenas
    ccq = models.FloatField(null=True, blank=True)
    power = models.FloatField(null=True, blank=True)
    signal = models.FloatField(null=True, blank=True)
    noise = models.FloatField(null=True, blank=True)
    tx_capacity = models.BigIntegerField(null=True, blank=True)		# Capacidad tx
    rx_capacity = models.BigIntegerField(null=True, blank=True)		# Capacidad rx
	
    class Meta:
        verbose_name = 'Hostórico general del dispositivo'
        verbose_name_plural = 'Hostóricoss generales de dispositivos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]



class Alarma(models.Model):
    """
    Alarma detectada por el servicio de monitorización a partir de una regla.

    Nace 'activa' cuando la regla se cumple y se resuelve cuando deja de
    cumplirse. La integración con Telegram/WhatsApp está prevista para el
    futuro, leyendo las alarmas 'activas'.
    """
    class Tipo(models.TextChoices):
        SNMP = 'snmp', 'SNMP'
        PING = 'ping', 'PING'
        MKT = 'mkt', 'MKT'

    class Estado(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        RESUELTA = 'resuelta', 'Resuelta'

    device = models.ForeignKey('dispositivos.Dispositivo', on_delete=models.CASCADE, related_name='alarmas',)

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.SNMP, blank=True, null=True, verbose_name='Tipo de alarma')
    regla = models.CharField(max_length=50, verbose_name='Regla')
    titulo = models.CharField(max_length=255, blank=True, verbose_name='Título')
    texto = models.TextField(blank=True, verbose_name='Detalle')
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVA, verbose_name='Estado',
    )
    sys_error = models.CharField(max_length=255, blank=True, null=True, verbose_name='Error sistema')
    creada_en = models.DateTimeField(auto_now_add=True, verbose_name='Detectada')
    resuelta_en = models.DateTimeField(null=True, blank=True, verbose_name='Resuelta')

    class Meta:
        verbose_name = 'Alarma'
        verbose_name_plural = 'Alarmas'
        ordering = ['-creada_en']
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'tipo', 'regla'],
                condition=models.Q(estado='activa'),
                name='alarma_activa_por_regla',
            ),
        ]

    def __str__(self):
        return f'{self.device.nombre} · {self.regla} · {self.get_estado_display()}'


class OIDmetric(models.Model):
    """ Lista de todos los OID para una marca """

    class Tipo(models.TextChoices):
        GENERAL = 'general', 'General'
        PUERTOS = 'puertos', 'Puertos'
        PUERTOS_PON = 'puertos_pon', 'Puertos PON'
        WIFI = 'wifi', 'Estaciones WIFI'
        ONUS = 'onus', 'Estaciones ONU'
        COUNTER_WIFI = 'count_wifi', 'Contadores Estaciones'

    marca = models.ForeignKey('dispositivos.Marca', on_delete=models.CASCADE, related_name='oid')
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')

    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, default=Tipo.GENERAL, verbose_name='Tipo',
    )

    codigos = models.JSONField(
        default=dict, blank=True, null=True,
        verbose_name='Códigos OID',
        help_text='Códigos OID en formato JSon: {"uptime": "1.3.6.1.2.1.1.3.0",}<br>Consulte el modelo DeviceMetrics para los campos disponibles.',
    )

    class Meta:
        verbose_name = 'OIDmetric'
        verbose_name_plural = 'OIDmetrics'
        ordering = ['marca']

    def __str__(self):
        return f'{self.marca.nombre} {self.marca.modelo} {self.descripcion}'

