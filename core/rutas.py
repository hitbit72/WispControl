

def http_ruta(ruta, destino):
    """
    Funcion para obtener la ruta de retorno a partir de la URL anterior. Se usa para
    evitar que al editar o crear un router/plan, la página de detalle redirija
    correctamente a la lista en lugar de volver a la página de edición.
    """
    if any(palabra in ruta for palabra in ['editar', 'nuevo', 'eliminar']):
        return destino
    
    return ruta # Devuelve la ruta original
