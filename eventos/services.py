from .models import Evento


def registrar_evento(modulo, titulo, texto='', nivel=Evento.Nivel.INFO, id_dispositivo=None):
    """
    Función común para registrar un evento desde cualquier módulo de la
    aplicación (ej. `registrar_evento('mikrotik', 'Fallo', ..., nivel=Evento.Nivel.ERROR)`).
    """
    return Evento.objects.create(
        modulo=modulo,
        nivel=nivel,
        titulo=titulo,
        texto=texto,
        id_dispositivo=id_dispositivo,
    )