import os
import django

# 1. Configurar el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tu_proyecto.settings')

# 2. Inicializar Django
django.setup()

# 3. Importar el modelo después de inicializar Django
from dispositivos.models import Dispositivo, Interfaz
from metricas.models import DeviceMetrics, DeviceMetricHistory, InterfaceMetricHistory


def probar_consulta():
    print("Ejecutando consulta de prueba para Dispositivo...")
    
    try:
        # Ejemplo 1: Obtener todos los registros
        #dispositivos = Dispositivo.objects.all()
        #print(f"Total de dispositivos en la base de datos: {dispositivos.count()}")

        #for disp in dispositivos:
        #    print(f"- ID: {disp.id}, Nombre/Detalle: {disp}")

         
        dispositivo = Dispositivo.objects.filter(nombre = 'OLT 4P' ).first()
        print(f'nombre: {dispositivo.nombre}')

        # Ejemplo 2: Filtrar o buscar un registro específico (opcional)
        # primer_disp = Dispositivo.objects.first()
        # print(f"Primer dispositivo: {primer_disp}")
        
    except Exception as e:
        print(f"Ocurrió un error al consultar la base de datos: {e}")


if __name__ == '__main__':
    probar_consulta()