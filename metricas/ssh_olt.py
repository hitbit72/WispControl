import paramiko
import re, json

# Nombre de puertos que no se guardarán en la base de datos
EXCLUDE_PORT = ('veip','sit','nas','apcli','ip6tnl','gpondef','bcmsw','pon','wifi0','wifi1','lo','ubond','lag','teql','gre','rif','tunl','ppp1','ppp2','ppp3','ppp4','ppp5','ppp6','ppp7')


def procesar_sistema(dispositivo):
    final = False
    datos = {}
    datos['status'] = "error"
    conectado = False

    # conexion cliente SSH
    client = paramiko.SSHClient()
    # Opcional: Aceptar automáticamente la clave del servidor (host key)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote server
        client.connect(
            hostname=dispositivo.ip_gestion,
            port=22,
            username='ubnt',
            password=dispositivo.password,
            timeout=5,  # Tiempo máximo para la conexión TCP
            banner_timeout=10,  # Tiempo máximo para esperar el banner SSH del equipo
            # Alternatively, use key_filename='/path/to/id_rsa'
        )
        conectado = True

    except Exception as e:
        print(f"SSH Error al conectar a {dispositivo.ip_gestion}: {e}")
        datos['status'] = "timeout"
        return final, datos

    if not conectado:
        datos['status'] = "timeout"
        return final, datos

    # Consulta de datos
    try:
        # Sistems: mem, cpu load
        stdin, stdout, stderr = client.exec_command("top -b -n 1 | sed '5q'")
        data1 = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # Tiempo de actividad
        stdin, stdout, stderr = client.exec_command('cat /proc/uptime')
        data2 = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # Puertos PON
        stdin, stdout, stderr = client.exec_command('sudo olt_ifctl get-gpon-port-stat')
        data3 = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # ONUS LIST STATUS
        stdin, stdout, stderr = client.exec_command('sudo olt_ifctl onu-list')
        data4 = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        final = True
        datos['status'] = "ok"

    except Exception as e:
        print(f"SSH Error ejecutar comandos en {dispositivo.ip_gestion}: {e}")
        print(f"{salida_stderr}")
        datos['status'] = "error"

    finally:
        client.close()

    if final:
        datos = sistema(data1, data2)
        datos['puertos'] = gpon_port(data3)

    return final, datos



def sistema(p1, p2):
    datos = {}
    linea=1
    mem_total = 1
    mem_used = 1
    mem_free = 1
    cpu = 0
    upt = 0

    # Procesar la salida línea por línea de top: mem, cpu, load average
    linea = 1
    if p1:
        for line in p1.splitlines():
            print(line)
            print('-'*20)
            if linea == 1:
                match_cpu = re.search(r'load average:\s+([0-9.]+),\s+([0-9.]+),\s+([0-9.]+)', line)
                cpu = match_cpu.group(2) if match_cpu else 0
            elif linea == 4:
                match_mem = re.search(r'KiB Mem :\s+([0-9]+) total,\s+([0-9]+) free,\s+([0-9]+) used,\s+([0-9]+) buff', line)
                if match_mem:
                    mem_total = int(match_mem.group(1))
                    mem_free = int(match_mem.group(2))
                    mem_used = int(match_mem.group(3))
            linea += 1

    # Uptime
    if p2:
        upt = int(float(p2.split()[0]))

    datos['ram'] = round((mem_used / mem_total) * 100, 2)
    datos['cpu'] = float(cpu)
    datos['uptime'] = upt

    return datos


def gpon_port(p1):
    gpon_info = []
    data = json.loads(p1)
    ports_status = data.get("GET_PORT_STATUS", {})

    # Iterar sobre cada puerto (clave y valor)
    for nombre_puerto, info in ports_status.items():
        current_speed = info.get("currentSpeed", "")
        current_state = info.get("plugged", "down")
        if current_speed == "auto":
            current_speed = ""
        if current_state == True:
            current_state = "up"
        else:
            current_state = "down"
        if current_speed != "":
            current_speed = current_speed.split("-")[0]

        # Extraer rxBytes de forma segura (si no existe statistics o rxBytes, devuelve 0 o N/A)
        statistics = info.get("statistics", {})
        rx_bytes = statistics.get("rxBytes", 0)
        tx_bytes = statistics.get("txBytes", 0)

        gpon_info.append(
            {
                'nombre': nombre_puerto,
                'estado': current_state,
                'speed': current_speed,
                'rx_counter': rx_bytes,
                'tx_counter': tx_bytes
            }
        )

    return gpon_info
