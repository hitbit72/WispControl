"""
`manage.py monitorizar`: consulta por SNMP todos los dispositivos con IP de
gestión y comunidad, guarda una métrica por dispositivo y aplica alarmas.

Para ejecutarse cada minuto, planificar una tarea con el planificador del
SO o el worker de fondo del proyecto.

Ejemplo de crontab (cada minuto):

    */1 * * * * cd /ruta/wisp_portal && uv run manage.py monitorizar >> /var/log/wispcontrol/metricas.log 2>&1

Uso manual:

    uv run manage.py monitorizar
    python manage.py monitorizar

    -- Para una solo IP: (con o sin el igual, funciona los dos)
    python manage.py monitorizar --ip=192.168.25.50 // python manage.py monitorizar --ip 192.168.25.50

Si quieres confirmar qué hay realmente en esa columna:

    uv run manage.py shell -c "from dispositivos.models import Dispositivo; [print(d.nombre, repr(d.snmp_community)) for d in Dispositivo.objects.all()]"

"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from dispositivos.models import Dispositivo

from metricas import snmp_client
from metricas.models import DeviceMetrics
from metricas.oids import oids_dispositivo
from metricas.services import evaluar_y_aplicar, guardar_metrica, guardar_puertos, guarda_staciones_wifi, guarda_estaciones_onu

# metrica OID -> campo del modelo (clave 'mem_total'/'mem_libre' -> ram).
# modelo DeviceMetrics
CAMPO = {
    'cpu': 'cpu',
    'ram': 'ram',
    'temperature': 'temperature',
    'power': 'power',
    'rx_dbm': 'rx_dbm',
    'tx_dbm': 'tx_dbm',
    'snr': 'snr',
    'ccq': 'ccq',
    'signal': 'signal',
    'frequency': 'frequency',
    'channel': 'channel',
    'clients': 'clients',
    'rx': 'rx',
    'tx': 'tx',
    'uptime': 'uptime',
    'w_channel': 'w_channel',
    'ssid': 'ssid',
    'antena': 'antena',
    'noise': 'noise',
    'sys_name': 'sys_name',
    'sys_descr': 'sys_descr',
    'version': 'version',
}

class Command(BaseCommand):
    help = 'Consulta SNMP a cada dispositivo y guarda métricas + alarmas.'

    def add_arguments(self, parser):
        # Añadimos un argumento opcional '--ip'
        parser.add_argument(
            '--ip',
            type=str,
            help='Filtrar y procesar únicamente un dispositivo por su IP de gestión.',
        )

    def handle(self, *args, **options):
        # Recuperamos el valor del argumento --ip si fue proporcionado
        ip_filtro = options.get('ip')

        if ip_filtro:
            dispositivos = (
                Dispositivo.objects
                .filter(ip_gestion=ip_filtro)
                .exclude(snmp_community__isnull=True)
            )
        else:
            dispositivos = (
                Dispositivo.objects
                .filter(ip_gestion__isnull=False)
                .exclude(snmp_community__isnull=True)
                .exclude(escanear=False)
            )

        # Si se pasó una IP, filtramos el queryset para que solo devuelva ese registro
        # if ip_filtro:
        #    dispositivos = dispositivos.filter(ip_gestion=ip_filtro)

        total = dispositivos.count()
        ok=0

        if not total:
            self.stdout.write(self.style.WARNING(
                'No hay dispositivos con IP de gestión.'))
        for dispositivo in dispositivos:
            if self._procesar(dispositivo):
                ok += 1
        self.stdout.write(self.style.SUCCESS(
            f'Monitorizados {ok} de {total} dispositivos.'))

    def _procesar(self, dispositivo):

        # Cargar los códigos OID para cada tipo de escaneo
        escalares_st = ''
        escalares_onu = ''

        escalares = oids_dispositivo(dispositivo, 'general')
        escalares_puerto = oids_dispositivo(dispositivo, 'puertos')

        # Solo los dispositivos AP y OLT
        if dispositivo.tipo.clave == 'ap':
            escalares_st = oids_dispositivo(dispositivo, 'wifi')
        if dispositivo.tipo.clave == 'olt':
            escalares_onu = oids_dispositivo(dispositivo, 'onus')
        
        try:
            resultado = snmp_client.consultar_escalares(dispositivo, escalares)
            #puertos = snmp_client.consultar_if_table2(dispositivo, escalares_puerto)
            puertos = snmp_client.consultar_if_table(dispositivo, escalares_puerto, 'puertos')
            estaciones = snmp_client.consultar_if_table(dispositivo, escalares_st, 'wifi')
            onus = snmp_client.consultar_if_table(dispositivo, escalares_onu, 'onus')
            status = DeviceMetrics.Status.OK
            #print(escalares_st)

        except snmp_client.SnmpError as exc:
            self.stdout.write(
                self.style.ERROR(f'[{dispositivo.ip_gestion}] {exc}'))
            resultado, puertos = {}, []
            estaciones, onus = [], []
            mensaje = str(exc).lower()
            status = (
                DeviceMetrics.Status.TIMEOUT
                if 'time out' in mensaje or 'timed out' in mensaje
                else DeviceMetrics.Status.ERROR
            )

        #print('RESULTADO --------------------')
        #print(resultado)
        datos = self._construir_datos(dispositivo, resultado)
        datos['puertos'] = puertos
        datos['estaciones'] = estaciones
        datos['onus'] = onus
        datos['status'] = status
        datos['timescan'] = timezone.now()

        #print(' DATOS --------------------')
        #print(f'Datos: {datos}')
        #print(f'Estaciones: {estaciones}')

        # guarda los datos en DeviceMetrics
        metrica = guardar_metrica(dispositivo, **datos)
        # Actualiza modelo de interfaz (puertos)
        guardar_puertos(dispositivo, **datos)
        # Actizalizar datos estaciones wifi y onus
        guarda_staciones_wifi(dispositivo, **datos)     # <-- Datos wifi de ubiquiti
        guarda_estaciones_onu(dispositivo, **datos)     # <-- Datos de ONU de OLT ubiquiti
        # evalua la alerta/alarma
        evaluar_y_aplicar(dispositivo, metrica)
        self.stdout.write(self.style.SUCCESS(
            f'[{dispositivo.nombre}] {status}'))
        return status == DeviceMetrics.Status.OK

    def _construir_datos(self, dispositivo, resultado):
        datos = {}
        if 'mem_total' in resultado and 'mem_libre' in resultado:
            total, _ = resultado['mem_total']
            libre, _ = resultado['mem_libre']
            if total:
                datos['ram'] = round((1 - libre / total) * 100, 2)

        for metrica, (numero, texto) in resultado.items():
            
            campo = CAMPO.get(metrica)
            #debug
            #print(f'{campo} - {metrica}: {numero} - {texto} ')

            if not campo:
                continue
            if metrica == 'uptime':
                # sysUpTime está en centésimas; MTIK en segundos.
                #valor = numero / 100 if dispositivo.marca != Dispositivo.Marcas.MIKROTIK else numero
                #datos['uptime'] = int(valor)
                datos['uptime'] = numero or 0
            elif campo == 'channel':
                datos['channel'] = numero or ''
            elif campo == 'temperature':
                if numero > 1000:
                    datos['temperature'] = numero / 1000
            elif numero is not None:
                datos[campo] = numero
                #print(f'es numero: {campo}: {numero}')
            elif texto is not None:
                datos[campo] = texto
                #print(f'es texto: {campo}: {texto}')
        return datos