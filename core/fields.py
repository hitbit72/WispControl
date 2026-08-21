"""
Campo de modelo que cifra su valor en la base de datos usando Fernet
(de la librería 'cryptography'). El cifrado/descifrado es transparente:
se usa igual que un CharField normal en el resto del código, incluido
el panel de administración.

Requiere la variable de entorno FIELD_ENCRYPTION_KEY (ver settings.py y
.env.example). Se puede generar una con:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

NOTA: si en el futuro se necesita cifrar otro campo fuera de esta app,
este módulo se puede mover a una ubicación compartida (ej. una app 'core').
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

def _get_fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise ImproperlyConfiguredEncryptionKey(
            "FIELD_ENCRYPTION_KEY no está configurada. Define esa variable en tu .env."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


class ImproperlyConfiguredEncryptionKey(Exception):
    pass


class EncryptedCharField(models.CharField):
    """
    CharField cuyo valor se guarda cifrado en la base de datos.

    El max_length declarado se usa tal cual para validar el valor en texto
    plano (ej. en formularios); la columna real en la base de datos necesita
    más espacio porque el texto cifrado ocupa más caracteres que el original.
    Por eso internamente se reserva espacio extra en la columna.
    """

    def db_type(self, connection):
        # El token cifrado (Fernet, base64) siempre ocupa más que el texto
        # original. Reservamos margen amplio para no quedarnos cortos.
        return f'varchar({max(self.max_length * 3, 255)})'

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        return _get_fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Valor guardado antes de activar el cifrado, o clave incorrecta.
            # Se devuelve tal cual en vez de romper la aplicación.
            return value
