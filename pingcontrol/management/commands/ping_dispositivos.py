"""
`manage.py ping_dispositivos`: hace ping a todos los dispositivos con ping=True
y guarda la latencia en DeviceMetrics. Actualiza estado y alarmas.

Para ejecutarse cada 5 minutos, planificar una tarea con cron:

    */5 * * * * cd /ruta/wisp_portal && uv run manage.py ping_dispositivos >> /var/log/wispcontrol/ping.log 2>&1

Uso manual:

    uv run manage.py ping_dispositivos
    python manage.py ping_dispositivos

    -- Para un solo dispositivo por IP:
    python manage.py ping_dispositivos --ip=192.168.25.50

    -- Para filtrar por tipo de dispositivo:
    python manage.py ping_dispositivos --tipo=ap
    python manage.py ping_dispositivos --tipo=router

    -- Combinado tipo con IP (aunque IP ya es único)
    python manage.py ping_dispositivos --ip=192.168.1.10 --tipo=ap

    -- Para filtrar por rol de dispositivo:
    python manage.py ping_dispositivos --rol=main   (solo acepta: main y station)

"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from dispositivos.models import Dispositivo
from pingcontrol.services import procesar_dispositivo


class Command(BaseCommand):
    help = 'Hace ping a dispositivos con ping=True y actualiza métricas/estado/alarmas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ip',
            type=str,
            help='Filtrar y procesar únicamente un dispositivo por su IP de gestión.',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            help='Filtrar dispositivos por tipo (clave del TipoEquipo, ej: ap, router, switch, olt, onu).',
        )
        parser.add_argument(
            '--rol',
            type=str,
            choices=['main', 'station'],
            help='Filtrar dispositivos por su rol (rol del Equipo: main, station).',
        )

    def handle(self, *args, **options):
        ip_filtro = options.get('ip')
        tipo_filtro = options.get('tipo')
        tipo_rol = options.get('rol')

        if ip_filtro:
            dispositivos = Dispositivo.objects.filter(
                ip_gestion=ip_filtro,
            )
        else:
            dispositivos = Dispositivo.objects.filter(
                ping=True,
                ip_gestion__isnull=False,
            )

        if tipo_filtro:
            dispositivos = dispositivos.filter(tipo__clave=tipo_filtro)

        if tipo_rol:
            dispositivos = dispositivos.filter(rol=tipo_rol)

        total = dispositivos.count()
        ok = 0
        errores = 0

        if not total:
            self.stdout.write(self.style.WARNING(
                f'[{timezone.now():%d/%m/%Y %H:%M:%S}] No hay dispositivos para comprobar.'))
            return

        # Bucle por los dispositivos
        for dispositivo in dispositivos:
            try:
                metrica, detectadas = procesar_dispositivo(dispositivo)
                if metrica.status_ping == metrica.Status.OK:
                    ok += 1
                    # self.stdout.write(self.style.SUCCESS(f'[{timezone.now():%d/%m/%Y %H:%M:%S}] 'f'[{dispositivo.ip_gestion}] Ping OK · {metrica.latencia} ms'))
                else:
                    errores += 1
                    self.stdout.write(self.style.ERROR(
                        f'[{timezone.now():%d/%m/%Y %H:%M:%S}] {dispositivo.ip_gestion} ({dispositivo.nombre}) Ping FALLÓ'))
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(
                    f'[{timezone.now():%d/%m/%Y %H:%M:%S}] {dispositivo.ip_gestion} ({dispositivo.nombre}) Error: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'[{timezone.now():%d/%m/%Y %H:%M:%S}] Procesados {total} dispositivos: {ok} OK, {errores} fallos.\n'))