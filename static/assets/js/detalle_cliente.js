

function mensajeModal(url_pk, nombre, opcion=null, tipo='contrato') {
    // Cambia el contenido del mensaje modal Ping
    const contenedor = document.getElementById('deleteModal');
    if (contenedor) {
        if (tipo == 'contrato') {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar contrato";
            let bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
            if (opcion){
                if ( opcion == 'pppoe' || opcion == 'sq'){
                    bm = `¿Seguro que quieres eliminar el contrato <strong>${nombre}</strong>?
                    <p class="mb-0 mt-2">Esto encola una tarea de <strong>baja</strong> para que el servicio MikroTik 
                    elimine el secret/queue correspondiente del router. La acción no se puede deshacer.</p>
                    `
                }
            }
            document.getElementById('deleteModalBody').innerHTML = bm;
            document.getElementById('deleteBtConfirm').href = url_pk;
        }
        if (tipo == 'dispositivo') {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar dispositivo";
            let bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
            if (opcion && opcion>0){
                bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
                <p class="mb-0 mt-2">Tiene <strong>${opcion} interfaz(es)</strong>
                que se eliminarán en cascada. La acción no se puede deshacer.</p>
                `
            }
            document.getElementById('deleteModalBody').innerHTML = bm;
            document.getElementById('deleteBtConfirm').href = url_pk;
        }
        mostrarModal('deleteModal', true);
    }
}


// Muestra modal
function mostrarModal(id){
    const alarmDv = document.getElementById(id);
    if (alarmDv) {
        let modalWin = new bootstrap.Modal(
        alarmDv,
        {}
        );
        modalWin.show();
    }
}

