"""
Señales que ejecuta un acción contra el mikrotik, si falla mantienen la cola 
de sincronización MikroTik al día cada vez que se crea, edita o elimina un Contrato.

Se encola la tarea y la ejecuta inmediatamente, si falla se ejecutará 
el servicio MikroTik (sincronizar_mikrotik.py) (proceso aparte) quien la procesa nuevamente más adelante.
Ver docs/mikrotik_proceso.md.
"""
from io import StringIO

from django.core.management import call_command
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from mikrotik.models import TareaSincronizacion
from mikrotik.services import encolar_tarea
from mikrotik.procesador import procesar_tarea
from mikrotik.management.commands.sincronizar_mikrotik import esta_ejecutandose

from eventos.models import Evento
from eventos.services import registrar_evento

from .models import Contrato

# Campos cuyo cambio implica avisar al router (además del identificador,
# que se compara aparte para detectar un renombrado).
CAMPOS_RELEVANTES = ('estado', 'plan_id', 'ip_asignada', 'pppoe_clave', 'conexion')

MODULO = 'clientes.contratos'

@receiver(pre_save, sender=Contrato)
def _guardar_valores_anteriores(sender, instance, **kwargs):
    """
    Antes de guardar, si el contrato ya existía, guarda una copia de sus
    valores actuales en la base de datos para poder compararlos en el
    post_save y decidir si hay que encolar una tarea.
    """
    if not instance.pk:
        instance._valores_anteriores = None
        return
    try:
        anterior = Contrato.objects.get(pk=instance.pk)
    except Contrato.DoesNotExist:
        instance._valores_anteriores = None
        return
    valores = {campo: getattr(anterior, campo) for campo in CAMPOS_RELEVANTES}
    valores['identificador_mikrotik'] = anterior.identificador_mikrotik
    instance._valores_anteriores = valores


@receiver(post_save, sender=Contrato)
def _sincronizar_al_guardar(sender, instance, created, **kwargs):
    if created:
        if instance.estado == Contrato.Estado.ACTIVO:
            encolar_tarea(instance, TareaSincronizacion.Operacion.ALTA)
            # Procesamos la tarea inmediatamente, si falla esta encolada para intentar más tarde
            #_sincronizar_mk(tarea, instance)
            _sincronizar_tarea()
        return

    anteriores = getattr(instance, '_valores_anteriores', None)
    if anteriores is None:
        # No se pudo comparar contra el valor anterior (caso raro). Se
        # encola de todas formas: es mejor una tarea de más, que el
        # servicio puede resolver comprobando el estado real del router,
        # que arriesgarse a perder un cambio real sin sincronizar.
        encolar_tarea(instance, TareaSincronizacion.Operacion.MODIFICACION)
        return

    identificador_cambio = anteriores.get('identificador_mikrotik') != instance.identificador_mikrotik
    cambio_relevante = any(
        anteriores.get(campo) != getattr(instance, campo) for campo in CAMPOS_RELEVANTES
    )

    if cambio_relevante or identificador_cambio:
        identificador_anterior = anteriores.get('identificador_mikrotik') if identificador_cambio else ''
        encolar_tarea(
            instance, TareaSincronizacion.Operacion.MODIFICACION, 
            identificador_anterior=identificador_anterior,
        )
        #_sincronizar_mk(tarea, instance)
        _sincronizar_tarea()


@receiver(post_delete, sender=Contrato)
def _sincronizar_al_eliminar(sender, instance, **kwargs):
    # 'instance' ya no existe en la base de datos en este punto (aunque el
    # objeto en memoria todavía tiene sus valores), así que la tarea se crea
    # sin vincular el FK — ver encolar_tarea().
    encolar_tarea(instance, TareaSincronizacion.Operacion.BAJA, vincular_contrato=False)

    # Ejecutamos la tarea encolada inmediatamente
    #_sincronizar_mk(tarea, instance)
    _sincronizar_tarea()


def _sincronizar_tarea():
    # Ejecuta el Command de sincronización, actulizando todas las tareas pendientes.
    # Se ha optado por esta opción porque puede haber otras tareas pendientes antes de la instancia actual.

    if esta_ejecutandose():
            print("sincronizar_tarea ya está corriendo")
            return
    
    out = StringIO()
    # Ejecuta el comando de forma segura e inicializada por Django
    call_command('sincronizar_mikrotik', stdout=out, stderr=out)


# No usado por ahora, ejecuta solo la tarea de la instancia actual
def _sincronizar_mk(tarea, contrato):
    """ Procesamos una tarea inmediatamente 
        si falla, al estar encolada, se intentará más adelante en sincronizar_mikrotik.py
    """
    if tarea:
        try:
            procesar_tarea(tarea)
            tarea.estado = TareaSincronizacion.Estado.COMPLETADA
            tarea.mensaje_error = ''
            tarea.procesada_en = timezone.now()
            tarea.save(update_fields=['estado', 'mensaje_error', 'procesada_en'])
            registrar_evento(
                MODULO,
                f'Contrato {contrato.nombre} · {tarea.get_operacion_display()} efectuada ({tarea.identificador_mikrotik})',
                f'{contrato.cliente.nombre_completo} - {tarea.plan_nombre} {tarea.get_operacion_display()} completada correctamente.',
                nivel=Evento.Nivel.INFO,
            )
        except Exception as exc:
            print(f'[FALLO] Tarea #{tarea.pk} {contrato.nombre} ({tarea.identificador_mikrotik}: {exc} ')
            pass