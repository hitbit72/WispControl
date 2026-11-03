import paramiko
import re, json

from mikrotik import client

# Nombre de puertos que no se guardarán en la base de datos
EXCLUDE_PORT = ('lag','gre')
# Puetos opticos
OPTIC_PORTS = ('pon','sfp','gpon')


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
        uptime = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # Hostname
        stdin, stdout, stderr = client.exec_command('hostname')
        host_name = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # Temepratura CPU
        stdin, stdout, stderr = client.exec_command('cat /sys/class/hwmon/hwmon1/device/temp1_input; cat /sys/class/hwmon/hwmon1/device/temp2_input; cat /sys/class/hwmon/hwmon1/device/temp3_input')
        cpuTemp = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # Puertos PON
        stdin, stdout, stderr = client.exec_command('sudo olt_ifctl get-gpon-port-stat')
        puertosOlt = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')

        # ONUS LIST STATUS
        stdin, stdout, stderr = client.exec_command('sudo olt_ifctl onu-list')
        onts = stdout.read().decode('utf-8')
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
        datos = sistema(data1, uptime, cpuTemp, host_name)
        datos['puertos'] = gpon_port(puertosOlt)
        datos['onus'] = onu_list(onts)

    return final, datos


# Procesa los datos SSH de la OLT 4P de ubiquiti
def sistema(sistema, uptime, cpuTemp, host_name):
    datos = {}
    linea=1
    mem_total = 1
    mem_used = 1
    mem_free = 1
    cpu = 0
    upt = 0

    # Procesar la salida línea por línea: mem, cpu, load average
    linea = 1
    if sistema:
        for line in sistema.splitlines():
            #print(line)
            #print('-'*20)
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
    if uptime:
        upt = int(float(uptime.split()[0]))

    # CPU Temp
    if cpuTemp:
        t1 = 0
        linea = 0
        for line in cpuTemp.splitlines():
            t1 += (float(line) /1000)
            linea += 1

        t1 = t1 / linea
        cpu_temp = t1

    datos['ram'] = round((mem_used / mem_total) * 100, 2)
    datos['cpu'] = float(cpu)
    datos['uptime'] = upt
    datos['sys_name'] = host_name.strip()
    datos['temperature'] = cpu_temp

    #print(datos)
    return datos


def gpon_port(p1):
    gpon_info = []
    data = json.loads(p1)
    ports_status = data.get("GET_PORT_STATUS", {})
    
    # Iterar sobre cada puerto (clave y valor)
    for nombre_puerto, info in ports_status.items():

        current_speed = info.get("currentSpeed", 0)
        if current_speed == "auto":
            current_speed = 0
        if current_speed != 0:
            current_speed = current_speed.split("-")[0]

        current_state = info.get("plugged", False)
        if current_state == True:
            current_state = "up"
        else:
            current_state = "down"

        # Extraer rxBytes de forma segura (si no existe statistics o rxBytes, devuelve 0 o N/A)
        statistics = info.get("statistics", {})
        rx_bytes = statistics.get("rxBytes", 0)
        tx_bytes = statistics.get("txBytes", 0)

        # Excluir puertos que contengan palabras clave en EXCLUDE_PORT
        if any(exclude in nombre_puerto for exclude in EXCLUDE_PORT):
            continue

        tipo_puerto = "Ethernet"
        if any(optic in nombre_puerto for optic in OPTIC_PORTS):
            tipo_puerto = "Óptico"

        #print(f"velocidad speed: {current_speed}")
        gpon_info.append(
            {
                'nombre': nombre_puerto.strip(),
                'estado': current_state,
                'speed': int(current_speed),
                'tipo': tipo_puerto,
                'rx_counter': rx_bytes,
                'tx_counter': tx_bytes
            }
        )

    return gpon_info


def onu_list(p1):
    onu_info = []
    data = json.loads(p1)
    onus_status = data.get("GET_ONU_LIST", [])

    for onu in onus_status:
        port_info = []

        # Crea la lista de Puertos de la ONU
        puertos = onu.get("ports", [])
        nPort = 1
        for puerto in puertos:
            # Extraer información de cada puerto
            port_state = puerto.get("plugged", "down")
            if port_state == True:
                port_state = "up"
            else:
                port_state = "down"
            speed = puerto.get("speed", "auto")
            if speed == "auto":
                speed = 0
            else:
                speed = speed.split("-")[0]

            port_info.append(
                {
                    'nombre': f'eth{puerto.get("id", {nPort})}',
                    'estado': port_state,
                    'speed': speed,
                }
            )
            nPort += 1

        # Extraer stadisticas puerto PON
        portsStat = onu.get("statistics", {})
        rxBytes = portsStat.get("rxBytes", 0)
        txBytes = portsStat.get("txBytes", 0)

        # Sistema
        sysStat = onu.get("system", {})
        cpu = sysStat.get("cpu", 0)
        mem = sysStat.get("mem", 0)
        uptime = sysStat.get("uptime", 0)
        temperature = sysStat.get("temperature", {})
        cpuTemp = float(temperature.get("cpu", 0))

        # IP de puerto PON
        wanStat = onu.get("router", {})
        wanIP = wanStat.get("wanAddress", "")
        if wanIP != "":
            wanIP = wanIP.split("/")[0]

        onu_info.append(
            {
                'serial': onu.get("serial", ""),
                'version': onu.get("firmwareVersion", ""),
                'signal': float(onu.get("rxPower", 0)),
                'power': float(onu.get("txPower", 0)),
                'pon': int(onu.get("oltPort", 0)),
                'distancia': int(onu.get("distance", 0)),
                'connected': onu.get("connected", ""),
                'uptime': uptime,
                'cpu': cpu,
                'mem': mem,
                'temperature': cpuTemp,
                'ip': wanIP,
                'mac': onu.get("mac", ""),
                'rx_counter': rxBytes,
                'tx_counter': txBytes,
                'puertos': port_info
            }
        )

    return onu_info