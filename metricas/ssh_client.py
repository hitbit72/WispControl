import paramiko
import re

# Nombre de puertos que no se guardarán en la base de datos
EXCLUDE_PORT = ('veip','sit','nas','apcli','ip6tnl','gpondef','bcmsw','pon','wifi0','wifi1','lo','ubond','lag','teql','gre','rif','tunl')

def procesar_sistema(dispositivo):
    final = False
    datos = {}
    datos['status'] = "error"

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
            # Alternatively, use key_filename='/path/to/id_rsa'
        )

        # Sistems: mem, cpu load
        #stdin, stdout, stderr = client.exec_command('top -b -n 1')
        stdin, stdout, stderr = client.exec_command("top -b -n 1 | sed '3q'")
        data1 = stdout.read().decode('utf-8')
        stdin, stdout, stderr = client.exec_command('cat /proc/uptime')
        data2 = stdout.read().decode('utf-8')
    
        # Puertos: nombre, mac, estado, ip
        #stdin, stdout, stderr = client.exec_command('ip -o addr show')
        stdin, stdout, stderr = client.exec_command('ip addr show')
        p1 = stdout.read().decode('utf-8')
        
        final = True
        datos['status'] = "ok"
    finally:
        client.close()

    datos = sistema(data1, data2)
    datos['puertos'] = puertos(p1)
    return final, datos



def sistema(p1, p2):
    datos = {}
    mem_total = 1
    mem_used = 1
    mem_free = 1
    cpu = 0
    upt = 0

    # Procesar la salida línea por línea de top: mem, cpu, load average
    linea = 1
    if p1:
        for line in p1.splitlines():
            parts = line.split()
            if len(parts) < 2 or linea > 3:
                continue

            #print(f'parts: {parts}')
            #print('-'*10)

            if parts[0] == 'Mem:':
                mem_used = int(parts[1].split('K')[0])
                mem_free = int(parts[3].split('K')[0])
                mem_total = mem_used + mem_free

            if parts[0] == 'Load':
                cpu = parts[3]

            linea += 1

    # Uptime
    if p2:
        upt = p2.split()[0]

    datos['ram'] = round((1 - mem_free / mem_total) * 100, 2)
    datos['cpu'] = cpu
    datos['uptime'] = upt
    return datos


def puertos(p1):
    # busca dstos de los puertos del comando ip addr show
    
    interfaces_info = []
    linea = 1

    # Procesar la salida por bloques
    bloques = re.split(r'\n(?=\d+:\s)', p1)
    #print(bloques)
    #print('-'*20)

    if p1:
        for bloque in bloques:
            if not bloque.strip():
                continue

            # 1. Extraer Nombre de la interfaz y State
            # Buscamos algo como "2: eth0: ..." y "state UP"
            match_header = re.search(r'^\d+:\s+([^:]+):.*state\s+([A-Z]+)', bloque)
            if not match_header:
                # Fallback si no encuentra el estado explícitamente en esa línea
                match_header = re.search(r'^\d+:\s+([^:]+):', bloque)
                iface_name = match_header.group(1) if match_header else 'Desconocido'
                state = ''
            else:
                iface_name = match_header.group(1)
                state = match_header.group(2)
                state = state.lower()

                # 2. Extraer MAC (link/ether)
                match_mac = re.search(r'link/ether\s+([0-9a-fA-F:]+)', bloque)
                mac = match_mac.group(1) if match_mac else ''

                # 3. Extraer la IP (inet) de esta interfaz (¿puede tener varias?)
                # Extrae la IP junto sin la máscara (ej: 192.168.1.15)
                #ips = re.findall(r'inet\s+([0-9.]+/\d+)', bloque)
                match_ip = re.search(r'inet\s+([0-9.]+)', bloque)
                ip = match_ip.group(1) if match_ip else ''

                # Guardar los datos estructurados
                if iface_name != '':
                    if not any(exclude.lower() in iface_name.lower() for exclude in EXCLUDE_PORT):
                        interfaces_info.append(
                            {
                                'nombre': iface_name,
                                'estado': state,
                                'mac': mac,
                                'ip': ip,
                            }
                        )

    return interfaces_info




def puertos1(p1):
    # Busca datos de los puertos de ifconfig
    interfaces_info = []
    
    iface_name = ''
    mac = ''
    ip = ''
    state = ''

    linea=1
    next_linea=0

    for line in p1.splitlines():
        parts = line.split()
        if len(parts) < 1:
            continue

        if len(parts)>3:
            if parts[3].lower() == 'hwaddr':
                iface_name = parts[0]
                mac = parts[4]
                next_linea = linea+1
            elif parts[3].lower() == 'protocol':
                iface_name = parts[0]
                mac = ''
                next_linea = linea+1

        if linea == next_linea:
            if parts[0] == 'inet':
                ip = parts[1].split(':')[1]
                next_linea = linea+1
            elif parts[0] == 'inet6':
                next_linea = linea+1
            else:
                state = parts[0].lower()
                next_linea = 0

        if linea == next_linea:
            state = parts[0].lower()
            next_linea = 0

        if next_linea == 0:
            # Guardar los datos estructurados
            if iface_name != '':
                if not any(exclude.lower() in iface_name.lower() for exclude in EXCLUDE_PORT):
                    interfaces_info.append(
                        {
                            'nombre': iface_name,
                            'estado': state,
                            'mac': mac,
                            'ip': ip,
                        }
                    )
            iface_name = ''
            mac = ''
            ip = ''
            state = ''

        linea +=1

    return interfaces_info