let intervalActualizacion;
let socket;
let ordenesVistas = new Set(); // Para trackear órdenes ya vistas
let ordenesCompletadas = 0;
let audioNotificacion;

document.addEventListener('DOMContentLoaded', function() {
    // Crear audio de notificación
    audioNotificacion = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE');
    
    cargarOrdenes();
    inicializarSocket();
    
    // Backup: Actualizar cada 60 segundos por si falla el socket
    intervalActualizacion = setInterval(cargarOrdenes, 60000);
});

function inicializarSocket() {
    // Conectar al servidor Socket.IO
    socket = io();
    
    socket.on('connect', function() {
        console.log('✅ Conectado al servidor WebSocket');
        actualizarEstadoConexion(true);
        
        // Unirse a la sala de cocineros
        socket.emit('join_cocinero', {
            session_id: window.sessionId
        });
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Desconectado del servidor WebSocket');
        actualizarEstadoConexion(false);
    });
    
    // Escuchar nuevas órdenes en tiempo real
    socket.on('nueva_orden', function(data) {
        console.log('🔔 Nueva orden recibida:', data);
        
        // Reproducir sonido de notificación
        if (audioNotificacion) {
            audioNotificacion.play().catch(e => console.log('No se pudo reproducir audio:', e));
        }
        
        // Mostrar notificación del navegador
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('🔔 Nueva Orden', {
                body: `Orden #${data.orden_id.substring(0, 8)} - ${data.orden.items.length} producto(s)`,
                icon: '/static/img/orden-icon.png',
                badge: '/static/img/badge-icon.png'
            });
        }
        
        // Recargar órdenes
        cargarOrdenes();
        
        // Incrementar contador de nuevas
        const nuevasEl = document.getElementById('ordenes-nuevas');
        nuevasEl.textContent = parseInt(nuevasEl.textContent) + 1;
    });
    
    // Escuchar cuando una orden es vista por otro cocinero
    socket.on('orden_vista', function(data) {
        console.log(`👁️ Orden ${data.orden_id} vista por ${data.cocinero}`);
        
        // Agregar a vistas y actualizar UI
        ordenesVistas.add(data.orden_id);
        
        // Actualizar la card visualmente
        const card = document.querySelector(`[data-orden-id="${data.orden_id}"]`);
        if (card && !card.classList.contains('vista')) {
            card.classList.add('vista');
            const badge = card.querySelector('.orden-badge-vista');
            if (badge) {
                badge.textContent = `✅ Vista por ${data.cocinero}`;
            }
        }
    });
    
    // Recibir órdenes actuales al conectarse
    socket.on('ordenes_actuales', function(data) {
        console.log('📋 Órdenes actuales recibidas:', data.ordenes.length);
        mostrarOrdenes(data.ordenes);
    });
    
    socket.on('error', function(data) {
        console.error('Error del servidor:', data.message);
        alert('Error: ' + data.message);
    });
    
    socket.on('success', function(data) {
        console.log('✅ Éxito:', data.message);
    });
}

function actualizarEstadoConexion(conectado) {
    const statusEl = document.getElementById('connection-status');
    if (conectado) {
        statusEl.textContent = '🟢 Conectado';
        statusEl.style.color = '#4caf50';
    } else {
        statusEl.textContent = '🔴 Desconectado';
        statusEl.style.color = '#f44336';
    }
}

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
    const esVista = ordenesVistas.has(orden.orden_id);
    card.className = `orden-card ${esVista ? 'vista' : 'nueva'}`;
    card.setAttribute('data-orden-id', orden.orden_id);
    
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
    
    const badgeVista = esVista ? 
        `<div class="orden-badge-vista">✅ Vista</div>` : 
        `<div class="orden-badge-nueva">🆕 Nueva</div>`;
    
    card.innerHTML = `
        <div class="orden-header">
            <div>
                <span class="orden-id">Orden #${orden.orden_id.substring(0, 8)}</span>
                ${badgeVista}
            </div>
            <span class="orden-tiempo">${tiempoTranscurrido}</span>
        </div>
        <div class="orden-cajero">Cajero: ${orden.cajero}</div>
        <div class="orden-items">
            ${itemsHTML}
        </div>
        ${notasHTML}
        <div class="orden-footer">
            <button class="btn-marcar-vista" onclick="marcarComoVista('${orden.orden_id}')" ${esVista ? 'disabled' : ''}>
                ${esVista ? '✅ Ya Vista' : '👁️ Marcar como Vista'}
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
    document.getElementById('ordenes-completadas').textContent = ordenesCompletadas;
    
    // Contar nuevas (no vistas)
    const nuevas = ordenes.filter(o => 
        o.status === 'pendiente' && !ordenesVistas.has(o.orden_id)
    ).length;
    document.getElementById('ordenes-nuevas').textContent = nuevas;
}

function marcarComoVista(ordenId) {
    // Agregar a vistas localmente
    ordenesVistas.add(ordenId);
    ordenesCompletadas++;
    
    // Emitir evento al servidor
    socket.emit('marcar_orden_vista', {
        orden_id: ordenId,
        session_id: window.sessionId
    });
    
    // Actualizar UI inmediatamente
    cargarOrdenes();
}

async function cerrarSesion() {
    if (!confirm('¿Cerrar sesión?')) {
        return;
    }
    
    try {
        // Desconectar socket
        if (socket) {
            socket.emit('leave_cocinero');
            socket.disconnect();
        }
        
        // Limpiar intervalo
        if (intervalActualizacion) {
            clearInterval(intervalActualizacion);
        }
        
        const response = await fetch('/api/cerrar-sesion', {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
    }
}

// Pedir permiso para notificaciones al cargar
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}