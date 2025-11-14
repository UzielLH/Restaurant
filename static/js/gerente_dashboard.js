// Variables globales
let productosData = [];
let categoriasData = [];
let ordenActual = [];
let clienteSeleccionado = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    inicializarGerente();
    configurarNavegacion();
    cargarCategorias();
    cargarProductos();
});

function inicializarGerente() {
    console.log('Gerente Dashboard inicializado');
}

// Navegación entre secciones
function configurarNavegacion() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remover active de todos
            navItems.forEach(nav => nav.classList.remove('active'));
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Activar el seleccionado
            this.classList.add('active');
            const sectionId = this.getAttribute('data-section');
            document.getElementById(sectionId).classList.add('active');
            
            // Cargar datos según la sección
            if (sectionId === 'productos') {
                cargarProductos();
            } else if (sectionId === 'descuentos') {
                cargarDescuentos();
            } else if (sectionId === 'ordenes') {
                inicializarSeccionOrdenes();
            } else if (sectionId === 'reportes') {
                cargarReportesRapidos();
            }
        });
    });
}

// ==================== GESTIÓN DE PLATILLOS ====================

async function cargarCategorias() {
    try {
        const response = await fetch('/api/productos');
        const data = await response.json();
        
        if (data.success) {
            const categorias = [...new Set(data.productos.map(p => p.categoria))];
            categoriasData = categorias;
            
            const selectCategoria = document.getElementById('filtro-categoria');
            const selectEditCategoria = document.getElementById('edit-producto-categoria');
            
            categorias.forEach(cat => {
                const option = `<option value="${cat}">${cat}</option>`;
                selectCategoria.insertAdjacentHTML('beforeend', option);
                selectEditCategoria.insertAdjacentHTML('beforeend', option);
            });
        }
    } catch (error) {
        console.error('Error al cargar categorías:', error);
    }
}

async function cargarProductos() {
    try {
        const response = await fetch('/api/productos');
        const data = await response.json();
        
        if (data.success) {
            productosData = data.productos;
            mostrarProductos(data.productos);
        }
    } catch (error) {
        console.error('Error al cargar productos:', error);
        mostrarAlerta('Error al cargar productos', 'error');
    }
}

function mostrarProductos(productos) {
    const grid = document.getElementById('productos-grid');
    
    if (productos.length === 0) {
        grid.innerHTML = '<p class="empty-message">No se encontraron productos</p>';
        return;
    }
    
    grid.innerHTML = productos.map(producto => `
        <div class="producto-card">
            <img src="${producto.img || 'https://via.placeholder.com/280x180'}" 
                 alt="${producto.nombre}" 
                 class="producto-img">
            <div class="producto-info">
                <span class="producto-categoria">${producto.categoria}</span>
                <h3>${producto.nombre}</h3>
                <p class="producto-descripcion">${producto.descripcion || 'Sin descripción'}</p>
                
                <div class="producto-precios">
                    <div class="precio-item">
                        <label>Costo</label>
                        <span>$${parseFloat(producto.costo).toFixed(2)}</span>
                    </div>
                    <div class="precio-item">
                        <label>Precio</label>
                        <span>$${parseFloat(producto.precio).toFixed(2)}</span>
                    </div>
                    <div class="precio-item">
                        <label>Margen</label>
                        <span>${calcularMargen(producto.costo, producto.precio)}%</span>
                    </div>
                </div>
                
                <span class="producto-status status-${producto.status === 'disponible' ? 'disponible' : 'fuera'}">
                    ${producto.status === 'disponible' ? '✓ Disponible' : '✗ Fuera de Servicio'}
                </span>
                
                <div class="producto-actions">
                    <button class="btn btn-primary" onclick="editarProducto(${producto.id})">
                        Editar
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function calcularMargen(costo, precio) {
    const margen = ((precio - costo) / precio) * 100;
    return margen.toFixed(1);
}

function editarProducto(id) {
    const producto = productosData.find(p => p.id === id);
    if (!producto) return;
    
    document.getElementById('edit-producto-id').value = producto.id;
    document.getElementById('edit-producto-nombre').value = producto.nombre;
    document.getElementById('edit-producto-categoria').value = producto.categoria;
    document.getElementById('edit-producto-costo').value = producto.costo;
    document.getElementById('edit-producto-precio').value = producto.precio;
    document.getElementById('edit-producto-puntos').value = producto.precio_puntos || '';
    document.getElementById('edit-producto-descripcion').value = producto.descripcion || '';
    document.getElementById('edit-producto-img').value = producto.img || '';
    document.getElementById('edit-producto-status').value = producto.status;
    
    actualizarMargenGanancia();
    
    document.getElementById('modal-editar-producto').style.display = 'block';
}

function actualizarMargenGanancia() {
    const costo = parseFloat(document.getElementById('edit-producto-costo').value) || 0;
    const precio = parseFloat(document.getElementById('edit-producto-precio').value) || 0;
    
    if (precio > 0) {
        const margen = calcularMargen(costo, precio);
        const ganancia = precio - costo;
        document.getElementById('margen-ganancia').value = 
            `${margen}% ($${ganancia.toFixed(2)})`;
    } else {
        document.getElementById('margen-ganancia').value = '';
    }
}

// Listeners para actualizar margen automáticamente
document.getElementById('edit-producto-costo')?.addEventListener('input', actualizarMargenGanancia);
document.getElementById('edit-producto-precio')?.addEventListener('input', actualizarMargenGanancia);

function cerrarModalEditarProducto() {
    document.getElementById('modal-editar-producto').style.display = 'none';
}

// Form submit para editar producto
document.getElementById('form-editar-producto')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const productoData = {
        id: document.getElementById('edit-producto-id').value,
        nombre: document.getElementById('edit-producto-nombre').value,
        categoria: document.getElementById('edit-producto-categoria').value,
        costo: parseFloat(document.getElementById('edit-producto-costo').value),
        precio: parseFloat(document.getElementById('edit-producto-precio').value),
        precio_puntos: parseInt(document.getElementById('edit-producto-puntos').value) || 0,
        descripcion: document.getElementById('edit-producto-descripcion').value,
        img: document.getElementById('edit-producto-img').value,
        status: document.getElementById('edit-producto-status').value
    };
    
    // TODO: Implementar endpoint para actualizar producto
    console.log('Actualizando producto:', productoData);
    mostrarAlerta('Producto actualizado exitosamente', 'success');
    cerrarModalEditarProducto();
    cargarProductos();
});

// ==================== GESTIÓN DE DESCUENTOS ====================

async function cargarDescuentos() {
    // TODO: Implementar carga de descuentos desde API
    console.log('Cargando descuentos...');
}

function mostrarModalDescuentoGerente() {
    document.getElementById('modal-descuento-titulo').textContent = 'Nuevo Descuento';
    document.getElementById('form-descuento-gerente').reset();
    document.getElementById('desc-id').value = '';
    document.getElementById('modal-descuento-gerente').style.display = 'block';
}

function cerrarModalDescuentoGerente() {
    document.getElementById('modal-descuento-gerente').style.display = 'none';
}

function actualizarEjemploDescuento() {
    const tipo = document.getElementById('desc-tipo').value;
    const valor = parseFloat(document.getElementById('desc-valor').value) || 0;
    const ejemplo = document.getElementById('ejemplo-descuento');
    
    if (tipo === 'porcentaje') {
        ejemplo.textContent = `Ejemplo: ${valor}% = $${(100 * valor / 100).toFixed(2)} de descuento en compra de $100`;
    } else {
        ejemplo.textContent = `Ejemplo: $${valor.toFixed(2)} de descuento fijo en cualquier compra`;
    }
}

document.getElementById('form-descuento-gerente')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const descuentoData = {
        codigo: document.getElementById('desc-codigo').value,
        nombre: document.getElementById('desc-nombre').value,
        tipo: document.getElementById('desc-tipo').value,
        valor: parseFloat(document.getElementById('desc-valor').value),
        fecha_inicio: document.getElementById('desc-fecha-inicio').value,
        fecha_fin: document.getElementById('desc-fecha-fin').value,
        activo: document.getElementById('desc-activo').checked
    };
    
    // TODO: Implementar endpoint para crear descuento
    console.log('Creando descuento:', descuentoData);
    mostrarAlerta('Descuento creado exitosamente', 'success');
    cerrarModalDescuentoGerente();
    cargarDescuentos();
});

// ==================== GENERAR ÓRDENES ====================

function inicializarSeccionOrdenes() {
    cargarCategoriasOrdenes();
    cargarProductosOrdenes();
}

function cargarCategoriasOrdenes() {
    const tabsContainer = document.getElementById('categoria-tabs');
    tabsContainer.innerHTML = `
        <div class="categoria-tab active" data-categoria="all">Todos</div>
        ${categoriasData.map(cat => `
            <div class="categoria-tab" data-categoria="${cat}">${cat}</div>
        `).join('')}
    `;
    
    // Event listeners para tabs
    document.querySelectorAll('.categoria-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.categoria-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const categoria = this.getAttribute('data-categoria');
            filtrarProductosOrdenes(categoria);
        });
    });
}

function cargarProductosOrdenes() {
    filtrarProductosOrdenes('all');
}

function filtrarProductosOrdenes(categoria) {
    const productos = categoria === 'all' 
        ? productosData.filter(p => p.status === 'disponible')
        : productosData.filter(p => p.categoria === categoria && p.status === 'disponible');
    
    const listContainer = document.getElementById('productos-orden-list');
    listContainer.innerHTML = productos.map(p => `
        <div class="producto-item-orden" onclick="agregarProductoOrden(${p.id})">
            <img src="${p.img || 'https://via.placeholder.com/60'}" class="producto-item-img">
            <div style="flex: 1;">
                <strong>${p.nombre}</strong>
                <div>$${parseFloat(p.precio).toFixed(2)}</div>
            </div>
            <button class="btn btn-primary btn-sm">+</button>
        </div>
    `).join('');
}

function agregarProductoOrden(productoId) {
    const producto = productosData.find(p => p.id === productoId);
    if (!producto) return;
    
    const itemExistente = ordenActual.find(item => item.id === productoId);
    
    if (itemExistente) {
        itemExistente.cantidad++;
    } else {
        ordenActual.push({
            id: producto.id,
            nombre: producto.nombre,
            precio: parseFloat(producto.precio),
            costo: parseFloat(producto.costo),
            cantidad: 1
        });
    }
    
    actualizarResumenOrden();
}

function actualizarResumenOrden() {
    const itemsList = document.getElementById('orden-items-list');
    
    if (ordenActual.length === 0) {
        itemsList.innerHTML = '<p class="empty-message">No hay productos en la orden</p>';
        document.getElementById('orden-subtotal').textContent = '$0.00';
        document.getElementById('orden-total').textContent = '$0.00';
        return;
    }
    
    itemsList.innerHTML = ordenActual.map((item, index) => `
        <div class="orden-item">
            <div>
                <strong>${item.nombre}</strong>
                <div>$${item.precio.toFixed(2)} x ${item.cantidad}</div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span>$${(item.precio * item.cantidad).toFixed(2)}</span>
                <button class="btn btn-sm" onclick="cambiarCantidad(${index}, -1)">-</button>
                <button class="btn btn-sm" onclick="cambiarCantidad(${index}, 1)">+</button>
                <button class="btn btn-sm" onclick="eliminarItemOrden(${index})">🗑️</button>
            </div>
        </div>
    `).join('');
    
    const subtotal = ordenActual.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    document.getElementById('orden-subtotal').textContent = `$${subtotal.toFixed(2)}`;
    document.getElementById('orden-total').textContent = `$${subtotal.toFixed(2)}`;
}

function cambiarCantidad(index, cambio) {
    ordenActual[index].cantidad += cambio;
    
    if (ordenActual[index].cantidad <= 0) {
        ordenActual.splice(index, 1);
    }
    
    actualizarResumenOrden();
}

function eliminarItemOrden(index) {
    ordenActual.splice(index, 1);
    actualizarResumenOrden();
}

function limpiarOrden() {
    if (confirm('¿Deseas limpiar toda la orden?')) {
        ordenActual = [];
        clienteSeleccionado = null;
        document.getElementById('orden-cliente-correo').value = '';
        document.getElementById('cliente-info-orden').innerHTML = '';
        document.getElementById('orden-notas').value = '';
        actualizarResumenOrden();
    }
}

async function buscarClienteOrden() {
    const correo = document.getElementById('orden-cliente-correo').value.trim();
    
    if (!correo) {
        mostrarAlerta('Ingresa un correo electrónico', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/buscar-cliente?correo=${encodeURIComponent(correo)}`);
        const data = await response.json();
        
        if (data.success) {
            clienteSeleccionado = data.cliente;
            document.getElementById('cliente-info-orden').innerHTML = `
                <div style="background: var(--bg-color); padding: 10px; border-radius: 8px; margin-top: 10px;">
                    <strong>${data.cliente.nombre}</strong>
                    <div>Puntos: ${data.cliente.puntos_acumulados}</div>
                </div>
            `;
        } else {
            mostrarAlerta('Cliente no encontrado', 'error');
            clienteSeleccionado = null;
            document.getElementById('cliente-info-orden').innerHTML = '';
        }
    } catch (error) {
        console.error('Error al buscar cliente:', error);
        mostrarAlerta('Error al buscar cliente', 'error');
    }
}

async function guardarOrdenGerente() {
    if (ordenActual.length === 0) {
        mostrarAlerta('Agrega productos a la orden', 'warning');
        return;
    }
    
    const ordenData = {
        items: ordenActual,
        cliente_id: clienteSeleccionado?.id || null,
        notas: document.getElementById('orden-notas').value
    };
    
    try {
        const response = await fetch('/api/crear-orden', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ordenData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarAlerta('Orden generada exitosamente', 'success');
            limpiarOrden();
        } else {
            mostrarAlerta(data.message || 'Error al generar orden', 'error');
        }
    } catch (error) {
        console.error('Error al guardar orden:', error);
        mostrarAlerta('Error al guardar orden', 'error');
    }
}

// ==================== REPORTES RÁPIDOS ====================

async function cargarReportesRapidos() {
    // TODO: Implementar carga de reportes
    console.log('Cargando reportes rápidos...');
}

// ==================== UTILIDADES ====================

function mostrarAlerta(mensaje, tipo) {
    alert(mensaje); // Implementar sistema de notificaciones mejorado
}

function cerrarSesionGerente() {
    if (confirm('¿Estás seguro de cerrar sesión?')) {
        fetch('/api/cerrar-sesion', { method: 'POST' })
            .then(() => window.location.href = '/')
            .catch(error => console.error('Error:', error));
    }
}

// Cerrar modales al hacer clic fuera
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};