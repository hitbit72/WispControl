function DelMsgModal(id, url_pk, nombre, opcion=null, tipo='dispositivo') {
    // Cambia el contenido del mensaje modal
    let bm='¿Seguro que quieres eliminar?';
    const contenedor = document.getElementById(id);
    if (contenedor) {
        if (tipo == "dispositivo"){
            document.getElementById('deleteModalTitle').innerHTML="Eliminar dispositivo";
            bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
            if (opcion && opcion > 0){
                bm = `¿Seguro que quieres eliminar el dispositivo <strong>${nombre}</strong>?
                <p class="mb-0 mt-2">Tiene <strong>${opcion} interfaz(es)</strong> 
                que se eliminarán en cascada. La acción no se puede deshacer.</p>`;
            }
        }else if (tipo == 'interfaz') {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar interfaz";
            bm = `¿Seguro que quieres eliminar la interfaz <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
        }else if (tipo == 'enlace') {
            document.getElementById('deleteModalTitle').innerHTML="Eliminar enlace";
            bm = `¿Seguro que quieres eliminar el enlace <strong>${nombre}</strong>?
            <p>La acción no se puede deshacer.</p>`;
        }

        document.getElementById('deleteModalForm').action = url_pk;
        document.getElementById('deleteModalBody').innerHTML = bm;
        mostrarModal(id);
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

function mensajeModalPing(id){
    // Cambia el contenido del mensaje modal Ping. id = contenedor del texto
    const contenedor = document.getElementById(id);
    if (contenedor) {
        contenedor.innerHTML = `
            <div class="modal-header">
                <h2 class="modal-title h5" id="confirmModalLabel">Ejecutando Ping </h2>
                <span class="spinner-border spinner-border-sm htmx-indicator" id="spinner-ping" role="status" aria-hidden="true"></span>
            </div>
            <div class="modal-body"><p>Se están ejecutando el ping al dispositivo, espere ...</p></div>
            <div class="modal-footer">
            </div>
        `;
    }
}

// Abre/Cierra modal de alarma
function modalAlert(id, ver=false) {
    const modalEl = document.getElementById(id);
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal){
            if (ver)
                modal.show();
            }else{
                modal.hide();
            }
    }
}


window.addEventListener('DOMContentLoaded', event => {

    document.body.addEventListener('cerrarMetricaModal', function () {
        // Cierra modal de mensaje actualizando metrica una vez terminado el proceso
        const modalEl = document.getElementById('metricaModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
    });


    // Muestra alarma si existe al iniciar la pantalla detalle dispositivo
    const alarmDv = document.getElementById("alarmDeviceDetail");
    if (alarmDv) {
        let alertDeviceDetail = new bootstrap.Modal(
        alarmDv,
        {}
      );
      alertDeviceDetail.show();
    }

});