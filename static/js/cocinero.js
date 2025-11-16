let intervalActualizacion;

document.addEventListener('DOMContentLoaded', function() {
    cargarOrdenes();
    
    // Actualizar cada 30 segundos
    intervalActualizacion = setInterval(cargarOrdenes, 30000);
});

async function cargarOrdenes() {
    try {
        const response = await fetch('/api/ordenes');
        const data = await response.json();
        
        if (data.success) {
            mostrarOrdenes(data.ordenes);
            actualizarEstadisticas(data.ordenes);
        }
    } catch (error) {
        console.error('Error al cargar órdenes:', error);
    }
}

function mostrarOrdenes(ordenes) {
    const grid = document.getElementById('ordenes-grid');
    grid.innerHTML = '';
    
    // Filtrar solo órdenes pendientes
    const ordenesPendientes = ordenes.filter(o => o.status === 'pendiente');
    
    if (ordenesPendientes.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-text">No hay órdenes pendientes</div>
            </div>
        `;
        return;
    }
    
    ordenesPendientes.forEach(orden => {
        const card = crearOrdenCard(orden);
        grid.appendChild(card);
    });
}

function crearOrdenCard(orden) {
    const card = document.createElement('div');
    card.className = 'orden-card';
    
    const tiempoTranscurrido = calcularTiempoTranscurrido(orden.fecha);
    
    let itemsHTML = '';
    orden.items.forEach(item => {
        itemsHTML += `
            <div class="item">
                <span class="item-nombre">${item.nombre}</span>
                <span class="item-cantidad">x${item.cantidad}</span>
            </div>
        `;
    });
    
    const notasHTML = orden.notas ? 
        `<div class="orden-notas">📝 ${orden.notas}</div>` : '';
    
    card.innerHTML = `
        <div class="orden-header">
            <span class="orden-id">Orden #${orden.orden_id.substring(0, 8)}</span>
            <span class="orden-tiempo">${tiempoTranscurrido}</span>
        </div>
        <div class="orden-items">
            ${itemsHTML}
        </div>
        ${notasHTML}
        <div class="orden-footer">
            <button class="btn-completar" onclick="marcarCompletada('${orden.orden_id}')">
                ✅ Marcar como Completada
            </button>
        </div>
    `;
    
    return card;
}

function calcularTiempoTranscurrido(fechaOrden) {
    const ahora = new Date();
    const fecha = new Date(fechaOrden);
    const diffMs = ahora - fecha;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Hace un momento';
    if (diffMins === 1) return 'Hace 1 minuto';
    if (diffMins < 60) return `Hace ${diffMins} minutos`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return 'Hace 1 hora';
    return `Hace ${diffHours} horas`;
}

function actualizarEstadisticas(ordenes) {
    const pendientes = ordenes.filter(o => o.status === 'pendiente').length;
    document.getElementById('ordenes-pendientes').textContent = pendientes;
    
    // Aquí podrías calcular órdenes completadas y tiempo promedio
    // si guardas esa información en tu sistema
    document.getElementById('ordenes-completadas').textContent = '0';
    document.getElementById('tiempo-promedio').textContent = '-';
}

async function marcarCompletada(ordenId) {
    if (!confirm('¿Marcar esta orden como completada?')) {
        return;
    }
    
    // Por ahora solo recargamos, pero podrías implementar
    // un endpoint específico para cambiar el estado
    alert('Orden completada ✅');
    cargarOrdenes();
}

async function cerrarSesion() {
    if (!confirm('¿Cerrar sesión?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/cerrar-sesion', {
            method: 'POST'
        });
        
        if (response.ok) {
            clearInterval(intervalActualizacion);
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
    }
}