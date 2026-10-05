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

    -- Para filtrar por rol de dispositivo:
    python manage.py monitorizar --rol main mkt   (solo acepta: main, station y mkt)

    -- para fgiltrar por tipo de consulta y rol:
    python manage.py monitorizar --zona general puertos --rol main

Si quieres confirmar qué hay realmente en esa columna:
    uv run manage.py shell -c "from dispositivos.models import Dispositivo; [print(d.nombre, repr(d.snmp_community)) for d in Dispositivo.objects.all()]"

"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from dispositivos.models import Dispositivo, dispositivos_ap

from metricas import snmp_client
from metricas.models import DeviceMetrics, DeviceMetricHistory, OIDmetric
from metricas.oids import oids_dispositivo
from metricas import services

# metrica OID -> campo del modelo (clave 'mem_total'/'mem_libre' -> ram).
# campos del modelo DeviceMetrics y DeviceMetricHistory 
CAMPO = {
    'cpu': 'cpu',
    'ram': 'ram',
    'temperature': 'temperature',
    'ccq': 'ccq',
    'power': 'power',
    'signal': 'signal',
    'noise': 'noise',
    'rx': 'rx',
    'tx': 'tx',
    'frequency': 'frequency',
    'clients': 'clients',
    'uptime': 'uptime',
    'w_channel': 'w_channel',
    'ssid': 'ssid',
    'antena': 'antena',
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
        parser.add_argument(
            '--rol',
            type=str,
            nargs='+',  # Acepta 1 o más valores separados por espacio
            choices=['main', 'station', 'mkt'],
            help='Filtrar dispositivos por su rol (ej: --rol main mkt).',
        )
        parser.add_argument(
            '--zona',
            type=str,
            nargs='+',  # Acepta 1 o más valores separados por espacio
            choices=['general', 'puertos', 'wifi', 'onus', 'puertos_pon'],
            help='Filtrar y procesar únicamente la zona selecioanda (ej: --zona general wifi).',
        )

    def handle(self, *args, **options):
        # Recuperamos el valor del argumento --ip si fue proporcionado
        ip_filtro = options.get('ip')
        tipo_rol = options.get('rol')
        tipo_zona = options.get('zona')

        # Zonas de escaneo, por defecto todas activas
        self.zonas = {'general': True,
                      'puertos': True,
                      'wifi': True,
                      'onus': True,
                      'puertos_pon': True}
        
        # Filtrar por tipo de zona si se paso el argumento
        if tipo_zona:
            # Mantiene True solo para las claves que existen dentro de la lista tipo_zona
            self.zonas = {zona: (zona in tipo_zona) for zona in self.zonas}
        else:
            tipo_zona = 'todas'

        if ip_filtro:
            dispositivos = (
                Dispositivo.objects
                .filter(ip_gestion=ip_filtro)
                .filter(estado='activo')
                .exclude(snmp_community__isnull=True)
            )
        else:
            dispositivos = (
                Dispositivo.objects
                .filter(ip_gestion__isnull=False)
                .filter(estado='activo')
                .exclude(snmp_community__isnull=True)
                .exclude(escanear=False)
            )

        # Si se pasó un ROL, filtramos el queryset para que solo devuelva esos registros
        if tipo_rol:
            # Usamos rol__in para filtrar por todos los roles pasados
            dispositivos = dispositivos.filter(rol__in=tipo_rol)
            #dispositivos = dispositivos.filter(rol=tipo_rol)
        else:
            tipo_rol = 'todos'

        total = dispositivos.count()
        ok=0
        errores = 0

        if not total:
            self.stdout.write(self.style.WARNING(
                f'[{timezone.localtime():%d/%m/%Y %H:%M:%S}] No hay dispositivos para comprobar.'))

        # Bucle para consultar SNMP
        for dispositivo in dispositivos:
            if self._procesar(dispositivo):
                ok += 1
            else:
                errores += 1

        self.stdout.write(self.style.SUCCESS(
            f'[{timezone.localtime():%d/%m/%Y %H:%M:%S}] Procesados {total} dispositivos: {ok} OK, {errores} fallos. Zona: {tipo_zona} - Rol: {tipo_rol}\n'))


    def _procesar(self, dispositivo):

        # Cargar los códigos OID para cada tipo de escaneo
        datos = {}
        status = DeviceMetrics.Status.TIMEOUT
        escalares_st = {}
        escalares_onu = {}
        escalares_puerto_pon = {}
        resultado = {}
        puertos, puertos_pon, estaciones, onus = [], [], [], []

        escalares_general = oids_dispositivo(dispositivo, OIDmetric.Tipo.GENERAL)
        escalares_puerto = oids_dispositivo(dispositivo, OIDmetric.Tipo.PUERTOS)

        # Solo los dispositivos main y tipo antenas
        if dispositivo.rol == 'main':
            if dispositivo.tipo.clave in dispositivos_ap:
                escalares_st = oids_dispositivo(dispositivo, OIDmetric.Tipo.WIFI)

        # Puertos, OID especiales para OLT
        if dispositivo.tipo.clave == 'olt':
            escalares_puerto_pon = oids_dispositivo(dispositivo, OIDmetric.Tipo.PUERTOS_PON)
            escalares_onu = oids_dispositivo(dispositivo, OIDmetric.Tipo.ONUS)

        try:
            if self.zonas['general']:
                resultado = snmp_client.consultar_escalares(dispositivo, escalares_general)
            if self.zonas['puertos']:
                puertos = snmp_client.consultar_if_table(dispositivo, escalares_puerto, OIDmetric.Tipo.PUERTOS)
            if self.zonas['wifi']:
                if escalares_st:
                    estaciones = snmp_client.consultar_if_table(dispositivo, escalares_st, OIDmetric.Tipo.WIFI)
            if self.zonas['puertos_pon']:
                if escalares_puerto_pon:
                    puertos_pon = snmp_client.consultar_if_table(dispositivo, escalares_puerto_pon, OIDmetric.Tipo.PUERTOS)
            if self.zonas['onus']:
                if escalares_onu:
                    onus = snmp_client.consultar_if_table(dispositivo, escalares_onu, OIDmetric.Tipo.ONUS)
            status = DeviceMetrics.Status.OK

        except snmp_client.SnmpError as exc:
            self.stdout.write(
                self.style.ERROR(
                    f'[{timezone.localtime():%d/%m/%Y %H:%M:%S}] {dispositivo.ip_gestion} {exc}'))
            resultado = {}
            puertos, puertos_pon, estaciones, onus = [], [], [], []
            mensaje = str(exc).lower()
            status = (
                DeviceMetrics.Status.TIMEOUT
                if 'time out' in mensaje or 'timed out' in mensaje
                else DeviceMetrics.Status.ERROR
            )

        #print('RESULTADO --------------------')
        #print(resultado)
        if resultado:
            datos = self._construir_datos(dispositivo, resultado)
        if puertos:
            datos['puertos'] = puertos
        if puertos_pon:
            datos['puertos_pon'] = puertos_pon
        if estaciones:
            datos['estaciones'] = estaciones
        if onus:
            datos['onus'] = onus
        datos['status'] = status
        datos['timescan'] = timezone.now()

        # recuperar el estado anterio para evalua la alerta/alarma
        metrica_anterior = (
            DeviceMetrics.objects.filter(device=dispositivo)
            .order_by('-pk').first()
        )
        # Version historico, recuperar metricas historicas anteriores para evalua la alerta/alarma
        historico_anterior = (
            DeviceMetricHistory.objects.filter(device=dispositivo)
            .order_by('-timestamp').first()
        )
        # guarda los datos en DeviceMetrics y  DeviceMetricHistory
        # Variables para evaluar la alerta/alarma, si no hay datos anteriores se pasa None
        metrica = None
        historico = None
        if self.zonas['general']:
            if datos:
                metrica, historico = services.guardar_metrica(dispositivo, **datos)
        # Actualiza modelo de interfaz (puertos)
        if self.zonas['puertos']:
            if puertos:
                services.guardar_puertos(dispositivo, **datos)
        # Actizalizar datos estaciones wifi y onus
        if self.zonas['wifi']:
            if estaciones:
                services.guarda_staciones_wifi(dispositivo, **datos)     # <-- Datos wifi de ubiquiti
        if self.zonas['onus']:
            if onus:
                services.guarda_estaciones_onu(dispositivo, **datos)     # <-- Datos de ONU de OLT ubiquiti

        # evalua la alerta/alarma
        if self.zonas['general']:
            if metrica and historico:
                services.evaluar_y_aplicar(dispositivo, metrica, metrica_anterior, historico, historico_anterior)

        #self.stdout.write(self.style.SUCCESS(f'[{timezone.now():%d/%m/%Y %H:%M:%S}] {dispositivo.ip_gestion} ({dispositivo.nombre}) {status}'))
        return status == DeviceMetrics.Status.OK

    def _construir_datos(self, dispositivo, resultado):
        datos = {}
        # los dispositivos UBNT dan memoria_libre, en router MKT da memoria_ocupada
        if 'mem_total' in resultado:
            total, _ = resultado['mem_total']
            libre=1
            if total:
                if 'mem_libre' in resultado:
                    libre, _ = resultado['mem_libre']
                if 'mem_ocupada' in resultado:
                    ocupada, _ = resultado['mem_ocupada']
                    libre = total - ocupada
                if libre<=0:
                    libre=1
                datos['ram'] = round((1 - libre / total) * 100, 2)

        for metrica, (numero, texto) in resultado.items():
            
            campo = CAMPO.get(metrica)
            
            if not campo:
                continue
            if metrica == 'uptime':
                # sysUpTime está en centésimas; MTIK en segundos.
                #valor = numero / 100 if dispositivo.marca != Dispositivo.Marcas.MIKROTIK else numero
                #datos['uptime'] = int(valor)
                datos['uptime'] = numero or 0
            elif campo == 'temperature':
                datos['temperature'] = numero
                if datos['temperature'] > 1000:
                    datos['temperature'] = numero / 1000
            elif campo == 'antena':
                datos['antena'] = texto or numero
            elif numero is not None:
                datos[campo] = numero
                #print(f'es numero: {campo}: {numero}')
            elif texto is not None:
                datos[campo] = texto
                #print(f'es texto: {campo}: {texto}')
        return datos