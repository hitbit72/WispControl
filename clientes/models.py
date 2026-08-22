from django.db import models


class Cliente(models.Model):
    """Cliente final del WISP (persona o empresa) que contrata servicios."""

    class TipoDocumento(models.TextChoices):
        DNI = 'dni', 'DNI'
        CIF = 'cif', 'CIF'
        TIE = 'tie', 'TIE'
        NIE = 'nie', 'NIE'
        RUC = 'ruc', 'RUC / RFC / NIT'
        PASAPORTE = 'pasaporte', 'Pasaporte'
        OTRO = 'otro', 'Otro'

    nombre_completo = models.CharField(max_length=200, verbose_name='Nombre completo / Razón social')
    apodo = models.CharField(max_length=200, blank=True, verbose_name='Apodo / Mote')
    tipo_documento = models.CharField(max_length=20, choices=TipoDocumento.choices, default=TipoDocumento.DNI)
    numero_documento = models.CharField(max_length=30, blank=True, verbose_name='Número de documento')
    telefono = models.CharField(max_length=20, blank=True)
    telefono_alternativo = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    poblacion = models.ForeignKey('core.Poblacion', null=True, blank=True, on_delete=models.SET_NULL, related_name='clientes')
    direccion = models.CharField(max_length=255, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    fecha_alta = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre_completo',]

    def __str__(self):
        return f'{self.nombre_completo} · ({self.poblacion})'



class CuentaBancaria(models.Model):
    """ Cuanta/s bancaria/s de los clientes. Uncliente puede tener varias cuentas bancarias """

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cuenta_bancaria')
    nombre = models.CharField(max_length=255, verbose_name='Nombre Banco o Caja')
    numero_cuenta = models.CharField(max_length=200, verbose_name='Número de cuenta')

    class Meta:
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
        ordering = ['nombre',]

    def __str__(self):
        return f'{self.nombre} ({self.cliente.nombre_completo})'



class Contrato(models.Model):
    """Servicio contratado por un cliente. Un cliente puede tener varios contratos."""

    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        SUSPENDIDO = 'suspendido', 'Suspendido'
        CANCELADO = 'cancelado', 'Cancelado'
        PENDIENTE = 'pendiente', 'Pendiente'
        INSTALACION = 'instalacion', 'Pendiente de instalación'
        POTENCIAL = 'potencial', 'Cliente potencial'

    class Conexion(models.TextChoices):
        PPPOE = 'pppoe', 'PPPoE'
        SQ = 'sq', 'Simple Queue'
        DHCP = 'dhcp', 'DHCP'
        IP = 'ip', 'IP Fija'
        WIFI = 'wifi', 'WIFI'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contratos')
    nombre = models.CharField(max_length=100, verbose_name='Nombre del contrato')
    plan = models.ForeignKey('mikrotik.Plan', on_delete=models.PROTECT, related_name='contratos', verbose_name='Plan')
    precio_mensual = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.INSTALACION)
    fecha_inicio = models.DateField()
    fecha_cancelacion = models.DateField(null=True, blank=True)

    # Campos pensados para la integración con el servicio MikroTik.
    conexion = models.CharField(max_length=20, choices=Conexion.choices, default=Conexion.DHCP, verbose_name='Tipo de conexión')
    identificador_mikrotik = models.CharField(
        max_length=100, blank=True,
        verbose_name='Usuario MikroTik',
        help_text='Nombre del secret PPPoE o del simple queue en el router, según el tipo de conexión.',
    )
    pppoe_clave = models.CharField(max_length=100, blank=True, verbose_name='Clave PPPoE')
    ip_asignada = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='IP asignada',
        help_text='IP fija asignada, si es el caso')

    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.cliente.nombre_completo} · {self.plan.nombre}'
