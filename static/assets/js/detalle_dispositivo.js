function mensajeModalPing(){
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