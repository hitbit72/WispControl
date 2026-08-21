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

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.mysql'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'NAME': os.environ.get('DB_NAME', 'DBNAME'),
        'USER': os.environ.get('DB_USER', 'USERNAME'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'USERPASS*'),
    }
}


# --- Base de datos: PostgreSQL 'django.db.backends.postgresql' --------------------------------------------
"""
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE2', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME2', 'wisp_portal'),
        'USER': os.environ.get('DB_USER2', 'wisp_admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD2', ''),
        'HOST': os.environ.get('DB_HOST2', 'localhost'),
        'PORT': os.environ.get('DB_PORT2', '5432'),
    }
}
"""

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
