"""
Configuración de Django para el proyecto Portal WISP.

Fase actual: NÚCLEO
- Autenticación con roles (administrador / técnico / comercial)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# carga variables de entorno
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad -----------------------------------------------------------
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'clave-insegura-solo-para-desarrollo-cambiar-en-produccion'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps propias del núcleo
    'core',
    'accounts',
    'sector',
    'mikrotik',
    'eventos',
    'dispositivos',
    'clientes',
    'metricas',
    'pingcontrol',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Wisp_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'eventos.context_processors.notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'Wisp_portal.wsgi.application'
ASGI_APPLICATION = 'wisp_portal.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""


# --- Base de datos: MySQL 'django.db.backends.mysql' -------------------------------------------------
"""
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE1', 'django.db.backends.mysql'),
        'PORT': os.environ.get('DB_PORT1', '3306'),
        'HOST': os.environ.get('DB_HOST1', 'localhost'),
        'NAME': os.environ.get('DB_NAME1', 'DBNAME'),
        'USER': os.environ.get('DB_USER1', 'USERNAME'),
        'PASSWORD': os.environ.get('DB_PASSWORD1', 'USERPASS*'),
    }
}
"""

# --- Base de datos: PostgreSQL 'django.db.backends.postgresql' --------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'wisp_portal'),
        'USER': os.environ.get('DB_USER', 'wisp_admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# --- Usuario personalizado (con roles) ------------------------------------
AUTH_USER_MODEL = 'accounts.Usuario'

# --- Cifrado de campos sensibles (ej. clave API de routers MikroTik) ------
# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY')

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

# --- Internacionalización --------------------------------------------------
LANGUAGE_CODE = 'es'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'Europe/Madrid')
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Datos globales de MikroTik ---------------------------------------------
#
# Todo lo que puede variar por router o por plan (active_list, ppp_disable,
# parent, place-before, velocidades, prioridad) vive en los modelos Router y
# Plan, no aquí. Aquí solo va lo que es igual para todos los routers y planes.

MK_OPTIONS = {
    'BURST_LIMIT': '0/0',
    'BURST_THRESHOLD': '0/0',
    'BURST_TIME': '0s/0s',
    'BUCKET_SIZE': '0.1/0.1',
    'QUEUE_TYPE': 'cake-fibra/cake-fibra',
    'TOTAL_QUEUE': 'default',
}

# Intentos máximos antes de dejar una TareaSincronizacion como 'fallida'
# definitiva (a partir de ahí, solo se reintenta a mano desde el admin).
MK_MAX_INTENTOS = int(os.environ.get('MK_MAX_INTENTOS', '3'))



# --- Servicio de monitorización (metricas) ----------------------------------
#
# SNMP: valores por defecto del transporte. Cada dispositivo puede
# sobrescribirlos en Dispositivo.atributos_extra['snmp'].
METRICAS_SNMP = {
    'puerto': 161,
    'timeout': 2.0,
    'reintentos': 1,
}


# Umbrales de las reglas de alarma (ver metricas/reglas.py).
METRICAS_ALARMAS = {
    'cpu_max': 90,              # % CPU a partir del cual la CPU es alta
    'ram_max': 95,              # % RAM a partir del cual la RAM es alta
    'temp_max': 70,             # °C a partir del cual la temperatura es alta
    'puerto_caido': True,         # avisar con interfaz(es) abajo
    'sin_clientes_ap': True,      # avisar de AP sin clientes
    'cambio_frecuencia': True,    # avisar si cambia la frecuencia del enlace
    'cambio_canal': True,         # avisar si cambia el canal
    'caida_potencia_dbm': 20,   # dBm de bajada de Rx que dispara la alarma
    'caida_signal_dbm': 10,     # dBm de bajada de señal que dispara la alarma
    'caida_power_tx': 10,          # bajada de potencia de trasmision que dispara la alarma
}


# --- Control de Ping (pingcontrol) -------------------------------------------
# Configuración para el ping ICMP a dispositivos.
PING_CONTROL = {
    'count': 2,        # número de pings por dispositivo
    'timeout': 2,      # timeout en segundos por ping
    'interval': 0.2,   # intervalo entre pings en segundos
}
