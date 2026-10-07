
// Configuración común de gráficas
const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    scales: {
        x: {
            type: 'time',
            time: {
                unit: 'hour',
                displayFormats: {
                    hour: 'HH:mm',
                    day: 'dd/MM',
                    week: 'dd/MM',
                    month: 'dd/MM'
                }
            },
            title: { display: true, text: 'Tiempo' },
            grid: { display: false }
        },
        y: {
            beginAtZero: false,
            title: { display: true, text: 'Mbps' },
            grid: { color: 'rgba(0,0,0,0.05)' }
        }
    },
    plugins: {
        legend: { display: true, position: 'top' },
        tooltip: { 
            mode: 'index', 
            intersect: false,
            callbacks: {
                // Personaliza el título del tooltip para forzar el formato 24 horas
                title: function(tooltipItems) {
                    if (!tooltipItems.length) return '';
                    
                    // Obtiene la fecha/timestamp del punto
                    const timestamp = tooltipItems[0].parsed.x;
                    const date = new Date(timestamp);
                    
                    // Formatea a 24 horas (ej: 04/10/2026, 13:35:05)
                    const fecha = date.toLocaleDateString('es-ES', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    });
                    
                    const hora = date.toLocaleTimeString('es-ES', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false // Forzar formato 24h
                    });

                    return `${fecha} ${hora}`;
                },
                // formateador de etiquetas (Mbps, Kbps, etc.)
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    const val = context.parsed.y;
                    if (val === null || val === undefined) return label;

                    // Si es tráfico en bps (RX / TX bps)
                    if (context.dataset.label && context.dataset.label.includes('(bps)')) {
                        if (val >= 1e9) return label + (val / 1e9).toFixed(2) + ' Gbps';
                        if (val >= 1e6) return label + (val / 1e6).toFixed(2) + ' Mbps';
                        if (val >= 1e3) return label + (val / 1e3).toFixed(2) + ' Kbps';
                        return label + val.toFixed(0) + ' bps';
                    }

                    // Para el resto de métricas (CPU, RAM, dBm, ms, etc.)
                    return label + val.toFixed(2);
                }
            }
        }
    },
    elements: {
        line: { tension: 0.3, borderWidth: 1 },
        point: { radius: 0, hoverRadius: 5 }
    }
};

// Colores para datasets
const colors = {
    cpu: '#e74c3c',
    ram: '#3498db',
    temperature: '#f39c12',
    signal: '#2ecc71',
    ccq: '#9b59b6',
    noise: '#95a5a6',
    power: '#e67e22',
    capacity: '#8e44ad',
    latency: '#e67e22',
    rx: '#3498db',
    tx: '#e74c3c'
};

const labels_es = {
    cpu: 'CPU %',
    ram: 'RAM %',
    temperature: 'Temperatura °C',
    signal: 'Señal (dBm)',
    ccq: 'CCQ %',
    noise: 'Ruido (dBm)',
    power: 'Potencia (dBm)',
    capacity: 'Capacidad (Mbps)',
    latency_ms: 'Latencia (ms)',
    rx: 'RX (bps)',
    tx: 'TX (bps)'
};

// Calcular bps a partir de contadores acumulados
// los contadores SNMP ifHCInOctets / ifHCOutOctets están en bytes, por lo que
// para obtener bits por segundo tienes que multiplicar por 8
function calculateBps(data) {
    // data: array of {timestamp, rx, tx}
    if (!data || data.length < 2) return { labels: [], rx: [], tx: [] };
    
    const labels = [];
    const rxBps = [];
    const txBps = [];
    
    for (let i = 1; i < data.length; i++) {
        const prev = data[i - 1];
        const curr = data[i];
        
        const t1 = new Date(prev.timestamp).getTime();
        const t2 = new Date(curr.timestamp).getTime();
        const deltaTimeSec = (t2 - t1) / 1000;
        
        if (deltaTimeSec <= 0) continue;
        
        const deltaRx = (curr.rx ?? 0) - (prev.rx ?? 0);
        const deltaTx = (curr.tx ?? 0) - (prev.tx ?? 0);
        //console.log(curr.rx)

        // Solo valores positivos (contadores pueden reiniciarse)
        if (deltaRx < 0 || deltaTx < 0) continue;
        
        // Octetos -> bits
        const rxBpsValue = (deltaRx * 8) / deltaTimeSec;
        const txBpsValue = (deltaTx * 8) / deltaTimeSec;

        labels.push(curr.timestamp);
        rxBps.push(rxBpsValue);
        txBps.push(txBpsValue);
    }
    
    return { labels, rx: rxBps, tx: txBps };
}

// Render gráfica Tráfico Interfaces (con cálculo bps)
function renderTraficoChart() {
    const iface = document.getElementById('interface-select').value;
    if (!iface || !traficoInterfaces[iface]) return;
    
    const data = traficoInterfaces[iface];
    if (!data.length) return;
    
    // Calcular bps
    const { labels, rx, tx } = calculateBps(data);
    if (!labels.length) return;
    
    const ctx = document.getElementById('trafico-chart').getContext('2d');
    if (window['trafico-chartChart']) {
        window['trafico-chartChart'].destroy();
    }
    
    window['trafico-chartChart'] = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'RX (bps)',
                    data: labels.map((l, i) => ({ x: l, y: rx[i] })),
                    borderColor: colors.rx,
                    backgroundColor: colors.rx + '33',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'TX (bps)',
                    data: labels.map((l, i) => ({ x: l, y: tx[i] })),
                    borderColor: colors.tx,
                    backgroundColor: colors.tx + '33',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            ...commonOptions,
            plugins: {
                ...commonOptions.plugins,
                tooltip: {
                    ...commonOptions.plugins.tooltip,
                }
            },
            scales: {
                ...commonOptions.scales,
                y: { 
                    ...commonOptions.scales.y, 
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            if (value >= 1e9) return (value / 1e9).toFixed(1) + ' Gbps';
                            if (value >= 1e6) return (value / 1e6).toFixed(1) + ' Mbps';
                            if (value >= 1e3) return (value / 1e3).toFixed(1) + ' Kbps';
                            return value + ' bps';
                        }
                    }
                }
            }
        }
    });
}
