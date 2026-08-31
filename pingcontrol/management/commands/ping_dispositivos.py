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
"""

from django.core.management.base import BaseCommand

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

    def handle(self, *args, **options):
        ip_filtro = options.get('ip')

        if ip_filtro:
            dispositivos = Dispositivo.objects.filter(
                ip_gestion=ip_filtro,
            )
        else:
            dispositivos = Dispositivo.objects.filter(
                ping=True,
                ip_gestion__isnull=False,
            )

        total = dispositivos.count()
        ok = 0
        errores = 0

        if not total:
            self.stdout.write(self.style.WARNING(
                'No hay dispositivos con ping=True e IP de gestión.'))
            return

        # Bucle por los dispositivos
        for dispositivo in dispositivos:
            try:
                metrica, detectadas = procesar_dispositivo(dispositivo)
                if metrica.status == metrica.Status.OK:
                    ok += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'[{dispositivo.nombre}] Ping OK · {metrica.latencia} ms'))
                else:
                    errores += 1
                    self.stdout.write(self.style.ERROR(
                        f'[{dispositivo.nombre}] Ping FALLÓ · {metrica.sys_name or "Sin respuesta"}'))
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(
                    f'[{dispositivo.nombre}] Error: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'Procesados {total} dispositivos: {ok} OK, {errores} fallos.'))