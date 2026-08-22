"""
Conexión a un router MikroTik vía librouteros (API clásica, puerto 8728 /
8729 con SSL). No se conecta por REST API — ver la conversación de diseño
para el porqué (librouteros es más maduro y ya está probado para PPPoE
secrets, simple queues y address-lists).
"""

from contextlib import contextmanager
from librouteros import connect


@contextmanager
def conectar(router):
    """
    Context manager que abre una conexión a un Router MikroTik y la cierra
    al salir, incluso si algo fallo dentro del bloque 'with'.

    'router.clave' ya llega descifrada en texto plano — el propio campo del
    modelo (EncryptedCharField) se encarga de eso al leerlo de la base de
    datos.

    Uso:
        with conectar(router) as api:
            secrets = api.path('ppp', 'secret')
            ...
    """
    api = connect(
        username=router.usuario,
        password=router.clave,
        host=router.ip,
        port=router.puerto,
    )
    try:
        yield api
    finally:
        cerrar = getattr(api, 'close', None)
        if callable(cerrar):
            cerrar()
