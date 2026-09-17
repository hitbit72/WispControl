function DelMsgModal(id, url_pk, nombre, opcion=null, tipo='contrato') {
    // Cambia el contenido del mensaje modal
    let bm="¿Seguro que quieres eliminar?";
    const contenedor = document.getElementById(id);
    if (contenedor) {
        if (tipo == 'sector') {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar contrato";
            bm = `¿Seguro que quieres eliminar el sector <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
            if (opcion){
                if ( opcion > 0 ){
                    bm = `¿Seguro que quieres eliminar el sector <strong>${nombre}</strong>?
                    <p class="mb-0 mt-2">Tiene <strong>${opcion} dispositivo(s)</strong>, 
                    que quedarán sin sector, no se borrarán. 
                    La acción no se puede deshacer.</p>`;
                }
            }
        }else if (tipo == "dispositivo") {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar dispositivo";
            bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
            if (opcion){
                if (opcion > 0){
                    bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
                    <p class="mb-0 mt-2">Tiene <strong>${opcion} interfaz(es)</strong> 
                    que se eliminarán en cascada. La acción no se puede deshacer.</p>`;
                }
            }
        }

        document.getElementById('deleteModalForm').action = url_pk;
        document.getElementById('deleteModalBody').innerHTML = bm;
        mostrarModal(id, true);
    }
}

