from django.db import models


class Marca(models.Model):
    """ 
    Marcas y modelos para los dispositivos.
    Los OID selecioanan la marca tambien aqui
    """
    nombre = models.CharField(max_length=255)
    modelo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre',]

    def __str__(self):
        return f'{self.nombre} {self.modelo}'


class TipoEquipo(models.Model):
    """ Tipos de dispositivos/equipos """
    nombre = models.CharField(max_length=100, unique=True, null=False,blank=False)
    clave = models.CharField(max_length=100, unique=True, null=False, blank=False, 
                             help_text='Clave identificativa (sin espacios ni caracteres especiales)',)

    class Meta:
        verbose_name = 'Tipo de equipo'
        verbose_name_plural = 'Tipos de equipos'
        ordering = ['nombre',]

    def __str__(self):
        return f'{self.nombre}'



class Dispositivo(models.Model):
    """
    Cualquier equipo de la red: nodo, router, switch, AP, OLT, ONU o antena de cliente.

    Los atributos específicos de cada marca o modelo (ej. modo de radio de un AP Ubiquiti, 
    o el tipo de licencia RouterOS) se guardan en 'atributos_extra' en vez de crear una 
    columna por cada caso.
    """

    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        INACTIVO = 'inactivo', 'Inactivo'
        MANTENIMIENTO = 'mantenimiento', 'En mantenimiento',
        INSTALACION = 'instalacion', 'En instalación',
        RETIRADO = 'retirado', 'Retirado'

    class Rol(models.TextChoices):
        MAIN = 'main', 'Principal'
        STATION = 'station', 'Estación'
        MASTER = 'master', 'PtP Master'
        SLAVE = 'slave', 'PtP Esclavo'
        OTRO = 'otro', 'Otro'

    # nombre o SSID es unico
    nombre = models.CharField(max_length=100, null=False, blank=False, help_text='Nombre identificativo del eqipo',)
    # nombre host unico
    nombre_host = models.CharField(unique=True, max_length=100, null=False, blank=False, verbose_name='Nombre Host')
    marca = models.ForeignKey(Marca, null=False, blank=False, on_delete=models.PROTECT, 
                              verbose_name='Merca y modelo', related_name='dispositivos')
    tipo = models.ForeignKey(TipoEquipo, null=False, blank=False, on_delete=models.PROTECT, 
                             verbose_name='Tipo de equipo', related_name='dispositivos')
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.OTRO, verbose_name='Modo operación')

    sector = models.ForeignKey('sector.Sector', on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='dispositivos')
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='dispositivos',)
    onu_ref = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='Numero de Serie ONU', 
                               help_text='Identificador del equipo ONU',)
    ip_gestion = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP de gestión')
    ip_publica = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP pública')
    mac_address = models.CharField(max_length=17, blank=True, verbose_name='Dirección MAC')
    firmware_version = models.CharField(max_length=50, blank=True)
    snmp_community = models.CharField(max_length=100, default='public', blank=True, null=True, verbose_name='Comunidad SNMP', help_text='Solo aplica a dispositivos que soporten SNMP. Ej. "public"')

    escanear = models.BooleanField(default=False, null=True, blank=True, verbose_name='Escanear SNMP')
    alarma = models.BooleanField(default=False, null=True, blank=True, verbose_name='Alarma SNMP')
    alarma_puerto = models.BooleanField(default=False, null=True, blank=True, verbose_name='Alarma puertos SNMP')
    ping = models.BooleanField(default=True, null=True, blank=True, verbose_name='Escanear PING')
    alarma_ping = models.BooleanField(default=True, null=True, blank=True, verbose_name='Alarma PING')
    
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_instalacion = models.DateField(null=True, blank=True)

    atributos_extra = models.JSONField(
        default=dict, blank=True, null=True,
        verbose_name='Atributos adicionales',
        help_text='OIDs específicos de la marca/modelo que no aplican a todos los dispositivos.',
    )
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} · {self.ip_gestion} ({self.get_rol_display()} · {self.tipo.nombre})'



class Interfaz(models.Model):
    """Interfaz de red de un dispositivo (puerto físico, radio, VLAN, etc.)."""

    class Tipo(models.TextChoices):
        ETHERNET = 'ethernet', 'Ethernet'
        WIRELESS = 'wireless', 'Inalámbrica'
        PPPOE = 'pppoe', 'PPPoE'
        VLAN = 'vlan', 'VLAN'
        OPTICO = 'opt', 'OPTICO'
        OTRO = 'otro', 'Otro'

    class Estado(models.TextChoices):
        ARRIBA = 'up', 'Conectado'
        ABAJO = 'down', 'Off line'
        DESCONOCIDO = 'desconocido', 'Desconocido'

    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='interfaces')
    nombre = models.CharField(max_length=100, help_text="Ej. 'eth1', 'wlan0', 'eth1.100'")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ETHERNET)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DESCONOCIDO)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    velocidad_mbps = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Interfaz'
        verbose_name_plural = 'Interfaces'
        unique_together = ('dispositivo', 'nombre')
        ordering = ['dispositivo', 'nombre']

    def __str__(self):
        return f'{self.dispositivo.nombre} · {self.nombre}'



class Enlace(models.Model):
    """
    Conexión lógica entre dos dispositivos (backbone, acceso o radioenlace).
    Sirve como base para, más adelante, dibujar el mapa de topología de red.
    """

    class Tipo(models.TextChoices):
        BACKBONE = 'backbone', 'Backbone'
        ACCESO = 'acceso', 'Acceso'
        RADIOENLACE = 'radioenlace', 'Radioenlace',
        TORNCAL = 'torncal', 'Torncal'

    dispositivo_origen = models.ForeignKey(
        Dispositivo, on_delete=models.CASCADE, related_name='enlaces_origen',
    )
    dispositivo_destino = models.ForeignKey(
        Dispositivo, on_delete=models.CASCADE, related_name='enlaces_destino',
    )
    interfaz_origen = models.ForeignKey(
        Interfaz, on_delete=models.SET_NULL, null=True, blank=True, related_name='enlaces_como_origen',
    )
    interfaz_destino = models.ForeignKey(
        Interfaz, on_delete=models.SET_NULL, null=True, blank=True, related_name='enlaces_como_destino',
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ACCESO)
    ancho_banda_mbps = models.PositiveIntegerField(null=True, blank=True)
    distancia_km = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    frecuencia_ghz = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        help_text='Solo aplica a radioenlaces.',
    )
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Enlace'
        verbose_name_plural = 'Enlaces'

    def __str__(self):
        return f'{self.dispositivo_origen.nombre} → {self.dispositivo_destino.nombre}'
