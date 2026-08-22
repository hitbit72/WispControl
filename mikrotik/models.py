from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.fields import EncryptedCharField


class Router(models.Model):
    """
    Router MikroTik gestionado por el portal. Guarda los datos de conexión
    que el servicio MikroTik (proceso Python independiente) usará para
    hablar con el equipo real vía API de RouterOS.

    'clave' se guarda cifrada en la base de datos (core.fields.py) porque
    da acceso administrativo completo al router — a diferencia de la clave
    PPPoE de los contratos, que se mantiene en texto plano.

    'active_list' y 'ppp_disable' viven aquí (por router) en vez de en
    settings.py, porque cada router puede tener sus propios nombres de
    lista/perfil configurados.
    """

    nombre = models.CharField(max_length=100, verbose_name='Nombre identificativo')
    modelo = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.CharField(max_length=100, verbose_name='Usuario API')
    clave = EncryptedCharField(max_length=100, verbose_name='Contraseña API (cifrada)')
    ip = models.GenericIPAddressField(verbose_name='IP del router')
    puerto = models.PositiveIntegerField(
        default=8728,
        verbose_name='Puerto API',
        help_text='8728 por defecto (API), 8729 si el router usa API-SSL.',
    )

    sector = models.ForeignKey('sector.Sector', on_delete=models.PROTECT, related_name='routers_mikrotik',)

    active_list = models.CharField(
        max_length=100, verbose_name='Lista usuarios activos',
        help_text="List de usuario activos del FW", blank=True, default='ACTIVE_USER'
    )
    ppp_disable = models.CharField(
        max_length=100, verbose_name='Perfil desactivados ',
        help_text="Nombre del perfil ppp de usuarios desactivados", blank=True, default='DISABLE_USER'
    )

    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Router MikroTik'
        verbose_name_plural = 'Routers MikroTik'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.ip})'



class Plan(models.Model):
    """
    Plan de servicio configurado en un router MikroTik específico
    (Simple Queue / Queue Tree). Cada plan pertenece a un único router,
    porque la configuración de colas (parent, address-list, etc.) depende
    de cómo esté armado ese equipo en particular.

    Se referencia desde Contrato en vez de escribir velocidad y nombre a
    mano, para evitar errores de tipeo y que el plan real del router y el
    plan asignado al cliente no queden desincronizados.
    """

    router = models.ForeignKey(Router, on_delete=models.SET_NULL, null=True, related_name='planes')
    nombre = models.CharField(max_length=100)

    velocidad_bajada = models.PositiveIntegerField(
        verbose_name='Velocidad de bajada (Mbps)',
        help_text="Velocidad máxima de bajada (Mbps)."
    )
    velocidad_subida = models.PositiveIntegerField(
        verbose_name='Velocidad de subida (Mbps)',
        help_text="Velocidad máxima de subida (Mbps)."
    )

    # Configuración específica de la cola en RouterOS.
    parent = models.CharField(
        max_length=100, blank=True,
        verbose_name='Cola padre Queue',
        help_text="Interfaz o cola padre en el Queue Tree del router.",
    )
    before = models.CharField(
        max_length=100, blank=True,
        verbose_name='Insertar antes de',
        help_text="Nombre de la cola existente antes de la cual se inserta esta (orden en RouterOS).",
    )
    addr_list = models.CharField(
        max_length=100, blank=True,
        verbose_name='Address list',
        help_text="Nombre de la address-list del FW RouterOS asociada a este plan.",
    )
    limit_down = models.PositiveIntegerField(default=8, verbose_name='Limite de bajada (Mbps)')
    limit_up = models.PositiveIntegerField(default=3, verbose_name='Limite de subida (Mbps)')
    priority_down = models.PositiveIntegerField(
        default=6, validators=[MinValueValidator(1), MaxValueValidator(8)],
        help_text="Prioridad de RouterOS (1 a 8, donde 1 es la más alta).",
    )
    priority_up = models.PositiveIntegerField(
        default=6, validators=[MinValueValidator(1), MaxValueValidator(8)],
        help_text="Prioridad de RouterOS (1 a 8, donde 1 es la más alta).",
    )

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['router', 'nombre']
        unique_together = ('router', 'nombre')

    def __str__(self):
        return f'{self.nombre} · {self.router.nombre} ({self.velocidad_bajada}/{self.velocidad_subida} Mbps)'



class TareaSincronizacion(models.Model):
    """
    Cola de sincronización entre un Contrato y el router MikroTik real.

    Django solo crea filas aquí al guardar/borrar un Contrato — nunca llama
    al router directamente. El servicio MikroTik (proceso Python
    independiente) procesa las tareas 'pendiente', las pasa a 'procesando'
    y las deja en 'completada' o 'fallida', para no acoplar la velocidad o
    disponibilidad del router a la del portal.

    'contrato' es SET_NULL (no CASCADE): en una baja por eliminación real del
    contrato, la tarea tiene que sobrevivir al borrado para que el servicio
    la pueda procesar y avisarle al router. Por eso 'identificador_mikrotik'
    y 'conexion' se guardan como copia en el momento de encolar la tarea, en
    vez de leerse siempre desde el contrato (que puede ya no existir).

    Ver docs/mikrotik_proceso.md para el detalle completo del proceso.
    """

    class Operacion(models.TextChoices):
        ALTA = 'alta', 'Alta'
        MODIFICACION = 'modificacion', 'Modificación'
        BAJA = 'baja', 'Baja'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PROCESANDO = 'procesando', 'Procesando'
        COMPLETADA = 'completada', 'Completada'
        FALLIDA = 'fallida', 'Fallida'

    contrato = models.ForeignKey(
        'clientes.Contrato', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tareas_mikrotik',
    )
    plan_nombre = models.CharField(
        max_length=100, blank=True,
        help_text="Copia de contrato.plan.nombre en el momento de encolar la tarea",
    )
    router = models.ForeignKey(
        'mikrotik.Router', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tareas_sincronizacion',
        help_text='Copia de contrato.plan.router en el momento de encolar la tarea: en una baja, el contrato puede ya no existir y esta es la única forma de saber a qué router conectarse.',
    )
    identificador_mikrotik = models.CharField(
        max_length=100, blank=True,
        help_text='Copia del identificador en el momento de encolar la tarea (sobrevive aunque el contrato se elimine).',
    )
    conexion = models.CharField(
        max_length=20, blank=True,
        help_text="Copia de Contrato.conexion en el momento de encolar la tarea ('pppoe' o 'sq').",
    )
    estado_contrato = models.CharField(
        max_length=20, blank=True,
        help_text="Copia de Contrato.estado en el momento de encolar la tarea, para saber qué tipo de modificación se pidió (activo, suspendido, cancelado, etc.).",
    )
    operacion = models.CharField(max_length=20, choices=Operacion.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    identificador_anterior = models.CharField(
        max_length=100, blank=True,
        help_text='Solo se usa si la operación es una modificación que renombra el identificador.',
    )
    intentos = models.PositiveIntegerField(default=0)
    mensaje_error = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    procesada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tarea de sincronización MikroTik'
        verbose_name_plural = 'Tareas de sincronización MikroTik'
        ordering = ['-creada_en']

    def __str__(self):
        cliente = self.contrato.cliente.nombre_completo if self.contrato else '(contrato eliminado)'
        return f'{cliente} · {self.identificador_mikrotik} · {self.get_operacion_display()} · {self.get_estado_display()}'
