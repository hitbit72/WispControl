from django.db import models


class DeviceMetrics(models.Model):
    """
    Muestra periódica (SNMP) de un dispositivo en un instante concreto.
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
    timeping = models.DateTimeField(null=True, blank=True, verbose_name='Fecha escaneo Ping')

    sys_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Nombre sistema')
    sys_descr = models.CharField(max_length=255, null=True, blank=True, verbose_name='Descripción')
    version = models.CharField(max_length=255, null=True, blank=True, verbose_name='Versión')

    cpu = models.FloatField(null=True, blank=True, verbose_name='CPU (%)')
    ram = models.FloatField(null=True, blank=True, verbose_name='RAM (%)')
    temperature = models.FloatField(null=True, blank=True, verbose_name='Temperatura (°C)')

    power = models.FloatField(null=True, blank=True, verbose_name='Potencia (W)')
    rx_dbm = models.FloatField(null=True, blank=True, verbose_name='Rx (dBm)')
    tx_dbm = models.FloatField(null=True, blank=True, verbose_name='Tx (dBm)')
    rx = models.BigIntegerField(null=True, blank=True, verbose_name='Velocidad Rx (bps)')
    tx = models.BigIntegerField(null=True, blank=True, verbose_name='Velocidad Tx (bps)')
    uptime = models.PositiveBigIntegerField(
        null=True, blank=True,
        verbose_name='Uptime (segundos)',
        help_text='Segundos desde el último reinicio.',
    )
    ssid = models.CharField(max_length=200, null=True, blank=True)
    snr = models.FloatField(null=True, blank=True, verbose_name='SNR (dB)')
    ccq = models.FloatField(null=True, blank=True, verbose_name='CCQ (%)')
    signal = models.FloatField(null=True, blank=True, verbose_name='Señal (dBm)')
    frequency = models.FloatField(null=True, blank=True, verbose_name='Frecuencia (MHz)')
    channel = models.CharField(max_length=20, blank=True, verbose_name='Canal')
    noise = models.FloatField(null=True,blank=True, verbose_name='Noise floor')
    w_channel = models.FloatField(null=True,blank=True, verbose_name='Ancho canal')
    antena = models.CharField(max_length=100, null=True, blank=True, verbose_name='Tipo Antena')
    distancia = models.PositiveIntegerField(null=True, blank=True, verbose_name='Distnacia')
    clients = models.PositiveIntegerField(null=True, blank=True, verbose_name='Clientes conectados')
    latencia = models.FloatField(null=True, blank=True, verbose_name='Latencia')
    puertos = models.JSONField(
        default=list, blank=True,
        verbose_name='Interfaces',
        help_text='Lista JSON de {nombre, estado} de cada interfaz (estado: up/down).',
    )
    estaciones = models.JSONField(
        default=list, blank=True, null=True,
        verbose_name='Estaciones',
        help_text='Lista JSON de {ip, host, señal, ccq, noise, uptime} de cada estación.',
    )
    onus = models.JSONField(
        default=list, blank=True, null=True,
        verbose_name='Onus',
        help_text='Lista JSON de {ref, señal, pon, port_speed, uptime} de cada ONU fibra.',
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OK, verbose_name='Estado SNMP',)
    status_ping = models.CharField(max_length=20, choices=Status.choices, default=Status.OK, verbose_name='Estado PING',)

    class Meta:
        verbose_name = 'Métrica de dispositivo'
        verbose_name_plural = 'Métricas de dispositivos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp'], name='device_metrica_idx'),
        ]

    def __str__(self):
        return f'{self.device.nombre} · {self.timestamp:%d/%m/%Y %H:%M} · {self.status}'



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
                fields=['device', 'regla', 'estado'],
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
        WIFI = 'wifi', 'Estaciones WIFI'
        ONUS = 'onus', 'Estaciones ONU'

    marca = models.ForeignKey('dispositivos.Marca', on_delete=models.CASCADE, related_name='oid')
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')

    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, default=Tipo.GENERAL, verbose_name='Tipo',
    )

    codigos = models.JSONField(
        default=dict, blank=True, null=True,
        verbose_name='Códigos OID',
        help_text='Códigos OID en formato JSon: {"uptime": "1.3.6.1.2.1.1.3.0",}<br>sys_name, sys_descr, cpu, ram, temperature, power, rx_dbm, tx_dbm, rx, tx, uptime, ssid, snr, ccq, signal, frequency, channel, noise, w_channel,antena, clients, puertos, status',
    )

    class Meta:
        verbose_name = 'OIDmetric'
        verbose_name_plural = 'OIDmetrics'
        ordering = ['marca']

    def __str__(self):
        return f'{self.marca.nombre} {self.marca.modelo} {self.descripcion}'

