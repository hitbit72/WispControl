function mensajeModalPing(){
    // Cambia el contenido del mensaje modal Ping
    const contenedor = document.getElementById('pingData');
    if (contenedor) {
        contenedor.innerHTML = `
            <div class="modal-header">
                <h2 class="modal-title h5" id="confirmModalLabel">Ejecutando Ping </h2>
                <span class="spinner-border spinner-border-sm htmx-indicator" id="spinner-ping" role="status" aria-hidden="true"></span>
            </div>
            <div class="modal-body">Se están ejecutando el ping al dispositivo, espere ...</div>
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
        // Cierra modal de mensaje actualizando metrica
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