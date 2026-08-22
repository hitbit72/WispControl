"""
Procesa las tareas pendientes de TareaSincronizacion contra los routers
MikroTik reales. Pensado para ejecutarse vía cron cada cierto tiempo — NO
queda corriendo en bucle continuo, procesa lo que haya pendiente y termina.
Se pueda llamar, también, al generar un evento.

Ejemplo de crontab (cada 2 minutos):

    */2 * * * * cd /ruta/al/proyecto && uv run manage.py sincronizar_mikrotik >> /var/log/wispcontrol/mikrotik.log 2>&1

Uso manual:

    uv run manage.py sincronizar_mikrotik
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from mikrotik.models import TareaSincronizacion
from mikrotik.procesador import procesar_tarea
from eventos.models import Evento
from eventos.services import registrar_evento

MODULO = 'mikrotik'


class Command(BaseCommand):
    help = 'Procesa las tareas pendientes de sincronización con MikroTik (TareaSincronizacion).'

    def handle(self, *args, **options):
        max_intentos = getattr(settings, 'MK_MAX_INTENTOS', 3)

        tareas = TareaSincronizacion.objects.filter(
            Q(estado=TareaSincronizacion.Estado.PENDIENTE)
            | Q(estado=TareaSincronizacion.Estado.FALLIDA, intentos__lt=max_intentos)
        ).order_by('creada_en')

        if not tareas.exists():
            self.stdout.write('No hay tareas pendientes.')
            return

        for tarea in tareas:
            self._procesar_una(tarea, max_intentos)

    def _procesar_una(self, tarea, max_intentos):
        tarea.estado = TareaSincronizacion.Estado.PROCESANDO
        tarea.save(update_fields=['estado'])

        try:
            procesar_tarea(tarea)
        except Exception as exc:
            tarea.intentos += 1
            tarea.mensaje_error = str(exc)
            tarea.estado = TareaSincronizacion.Estado.FALLIDA
            tarea.procesada_en = timezone.now()
            tarea.save(update_fields=['intentos', 'mensaje_error', 'estado', 'procesada_en'])
            self.stderr.write(
                f'[FALLO] Tarea #{tarea.pk} ({tarea.identificador_mikrotik}, '
                f'intento {tarea.intentos}/{max_intentos}): {exc}'
            )
            # eventos: 3=error
            if tarea.intentos >= max_intentos:
                registrar_evento(
                    MODULO,
                    f'Tarea #{tarea.pk} fallida definitivamente ({tarea.identificador_mikrotik})',
                    f'Operación {tarea.get_operacion_display()} · {exc}',
                    nivel=Evento.Nivel.CRITICAL,
                )
            else:
                registrar_evento(
                    MODULO,
                    f'Intento {tarea.intentos}/{max_intentos} fallido en tarea #{tarea.pk}',
                    f'Operación {tarea.get_operacion_display()} ({tarea.identificador_mikrotik}) · {exc}',
                    nivel=Evento.Nivel.ERROR,
                )
        else:
            tarea.estado = TareaSincronizacion.Estado.COMPLETADA
            tarea.mensaje_error = ''
            tarea.procesada_en = timezone.now()
            tarea.save(update_fields=['estado', 'mensaje_error', 'procesada_en'])
            self.stdout.write(f'[OK] Tarea #{tarea.pk} ({tarea.identificador_mikrotik}) completada.')
            registrar_evento(
                MODULO,
                f'Tarea #{tarea.pk} sincronizada ({tarea.identificador_mikrotik})',
                f'Operación {tarea.get_operacion_display()} completada correctamente.',
                nivel=Evento.Nivel.INFO,
            )
