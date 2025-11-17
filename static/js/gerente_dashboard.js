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
    configurarFiltros();
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
                // Ya no necesitamos inicializar nada, solo mostrar la sección
                console.log('Sección de Punto de Venta cargada');
            }
        });
    });
}

function configurarFiltros() {
    // Filtro de búsqueda
    const searchInput = document.getElementById('buscar-producto');
    if (searchInput) {
        searchInput.addEventListener('input', filtrarProductos);
    }
    
    // Filtro de categoría
    const categoriaSelect = document.getElementById('filtro-categoria');
    if (categoriaSelect) {
        categoriaSelect.addEventListener('change', filtrarProductos);
    }
    
    // Filtro de estado
    const statusSelect = document.getElementById('filtro-status');
    if (statusSelect) {
        statusSelect.addEventListener('change', filtrarProductos);
    }
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

function filtrarProductos() {
    const searchTerm = document.getElementById('buscar-producto').value.toLowerCase();
    const categoriaFilter = document.getElementById('filtro-categoria').value;
    const statusFilter = document.getElementById('filtro-status').value;
    
    let productosFiltrados = [...productosData];
    
    // Filtrar por búsqueda
    if (searchTerm) {
        productosFiltrados = productosFiltrados.filter(p => 
            p.nombre.toLowerCase().includes(searchTerm) || 
            (p.descripcion && p.descripcion.toLowerCase().includes(searchTerm))
        );
    }
    
    // Filtrar por categoría
    if (categoriaFilter) {
        productosFiltrados = productosFiltrados.filter(p => 
            p.categoria === categoriaFilter
        );
    }
    
    // Filtrar por estado
    if (statusFilter) {
        productosFiltrados = productosFiltrados.filter(p => 
            p.status === statusFilter
        );
    }
    
    mostrarProductos(productosFiltrados);
}


async function cargarProductos() {
    try {
        const response = await fetch('/gerente/api/productos-gerente');
        const data = await response.json();
        
        if (data.success) {
            productosData = data.productos;
            mostrarProductos(data.productos);
        } else {
            alert('Error al cargar productos: ' + data.message);
        }
    } catch (error) {
        console.error('Error al cargar productos:', error);
        alert('Error al cargar productos');
    }
}

function mostrarProductos(productos) {
    const grid = document.getElementById('productos-grid');
    grid.innerHTML = '';
    
    if (productos.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">No hay productos registrados</p>';
        return;
    }
    
    productos.forEach(prod => {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        const estadoBadge = prod.status === 'disponible' ? 
            '<span class="badge badge-success">Disponible</span>' : 
            '<span class="badge badge-danger">No Disponible</span>';
        
        const imagen = prod.img || 'https://via.placeholder.com/200x150?text=Sin+Imagen';
        
        card.innerHTML = `
            <div class="product-image">
                <img src="${imagen}" alt="${prod.nombre}" onerror="this.src='https://via.placeholder.com/200x150?text=Sin+Imagen'">
            </div>
            <div class="product-info">
                <h3>${prod.nombre} ${estadoBadge}</h3>
                <p class="product-category">${prod.categoria}</p>
                <p class="product-description">${prod.descripcion || 'Sin descripción'}</p>
                <div class="product-pricing">
                    <div class="price-item">
                        <span class="price-label">Costo:</span>
                        <span class="price-value">$${parseFloat(prod.costo).toFixed(2)}</span>
                    </div>
                    <div class="price-item">
                        <span class="price-label">Precio:</span>
                        <span class="price-value primary">$${parseFloat(prod.precio).toFixed(2)}</span>
                    </div>
                    ${prod.precio_puntos ? `
                    <div class="price-item">
                        <span class="price-label">Puntos:</span>
                        <span class="price-value">${prod.precio_puntos} pts</span>
                    </div>
                    ` : ''}
                </div>
                <div class="product-actions">
                    <button class="btn btn-primary btn-sm" onclick="editarProducto(${prod.id})">
                        ✏️ Editar
                    </button>
                    ${prod.status === 'disponible' ? 
                        `<button class="btn btn-danger btn-sm" onclick="desactivarProducto(${prod.id})">
                            🚫 Desactivar
                        </button>` :
                        `<button class="btn btn-success btn-sm" onclick="activarProducto(${prod.id})">
                            ✅ Activar
                        </button>`
                    }
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

async function editarProducto(productoId) {
    try {
        const response = await fetch(`/gerente/api/productos/${productoId}`);
        const data = await response.json();
        
        if (data.success) {
            const producto = data.producto;
            
            // Cargar categorías primero
            await cargarCategoriasParaEdicion();
            
            // Llenar formulario con verificación de existencia
            const setValueSafe = (id, value) => {
                const element = document.getElementById(id);
                if (element) element.value = value || '';
            };
            
            setValueSafe('edit-producto-id', producto.id);
            setValueSafe('edit-producto-nombre', producto.nombre);
            setValueSafe('edit-producto-categoria', producto.categoria_id);
            setValueSafe('edit-producto-costo', parseFloat(producto.costo).toFixed(2));
            
            // Calcular ganancia a partir de costo y precio
            const costo = parseFloat(producto.costo);
            const precio = parseFloat(producto.precio);
            const costoConIVA = costo * 1.16;
            const ganancia = precio - costoConIVA;
            
            setValueSafe('edit-producto-ganancia', ganancia > 0 ? ganancia.toFixed(2) : '0.00');
            setValueSafe('edit-producto-puntos', producto.precio_puntos || '');
            setValueSafe('edit-producto-descripcion', producto.descripcion || '');
            setValueSafe('edit-producto-img', producto.img || '');
            setValueSafe('edit-producto-status', producto.status);
            
            // Actualizar calculadora de precio
            actualizarCalculadoraPrecio();
            
            document.getElementById('modal-editar-producto').style.display = 'block';
        }
    } catch (error) {
        console.error('Error al cargar producto:', error);
        alert('Error al cargar producto: ' + error.message);
    }
}

// Nueva función para actualizar la calculadora de precio
function actualizarCalculadoraPrecio() {
    const costo = parseFloat(document.getElementById('edit-producto-costo')?.value) || 0;
    const ganancia = parseFloat(document.getElementById('edit-producto-ganancia')?.value) || 0;
    
    if (costo > 0) {
        const costoConIVA = costo * 1.16;
        const precioFinal = costoConIVA + ganancia;
        
        // Actualizar previews
        const costoIVAPreview = document.getElementById('edit-costo-iva-preview');
        const precioCalculadoPreview = document.getElementById('edit-precio-calculado-preview');
        
        if (costoIVAPreview) {
            costoIVAPreview.textContent = `$${costoConIVA.toFixed(2)}`;
        }
        
        if (precioCalculadoPreview) {
            precioCalculadoPreview.textContent = `$${precioFinal.toFixed(2)}`;
        }
    } else {
        const costoIVAPreview = document.getElementById('edit-costo-iva-preview');
        const precioCalculadoPreview = document.getElementById('edit-precio-calculado-preview');
        
        if (costoIVAPreview) costoIVAPreview.textContent = 'Se calculará automáticamente';
        if (precioCalculadoPreview) precioCalculadoPreview.textContent = '$0.00';
    }
}
// Actualizar listeners para la calculadora
document.getElementById('edit-producto-costo')?.addEventListener('input', actualizarCalculadoraPrecio);
document.getElementById('edit-producto-ganancia')?.addEventListener('input', actualizarCalculadoraPrecio);

async function cargarCategoriasParaEdicion() {
    try {
        const response = await fetch('/gerente/api/categorias-gerente');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('edit-producto-categoria');
            select.innerHTML = '<option value="">Seleccionar categoría</option>';
            
            // Filtrar solo categorías activas
            const categoriasActivas = data.categorias.filter(cat => cat.activo);
            
            categoriasActivas.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.nombre;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error al cargar categorías:', error);
    }
}

// Manejar envío del formulario de edición
// Manejar envío del formulario de edición
document.getElementById('form-editar-producto')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const productoId = document.getElementById('edit-producto-id').value;
    const nombre = document.getElementById('edit-producto-nombre').value;
    const categoriaId = document.getElementById('edit-producto-categoria').value;
    const costo = parseFloat(document.getElementById('edit-producto-costo').value);
    const ganancia = parseFloat(document.getElementById('edit-producto-ganancia').value) || 0;
    
    // Calcular precio final usando la fórmula: Precio = (Costo × 1.16) + Ganancia
    const costoConIVA = costo * 1.16;
    const precio = costoConIVA + ganancia;
    
    const puntos = document.getElementById('edit-producto-puntos').value;
    const descripcion = document.getElementById('edit-producto-descripcion').value;
    const img = document.getElementById('edit-producto-img').value;
    const status = document.getElementById('edit-producto-status').value;
    
    if (!nombre || !categoriaId || !costo || isNaN(precio)) {
        alert('Por favor complete todos los campos obligatorios correctamente');
        return;
    }
    
    if (precio <= 0) {
        alert('El precio final debe ser mayor a 0');
        return;
    }
    
    try {
        const response = await fetch(`/gerente/api/productos/${productoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombre: nombre,
                categoria_id: parseInt(categoriaId),
                costo: parseFloat(costo.toFixed(2)),
                precio: parseFloat(precio.toFixed(2)),
                precio_puntos: puntos ? parseInt(puntos) : null,
                descripcion: descripcion,
                img: img,
                status: status
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Producto actualizado exitosamente\n\nCosto: $' + costo.toFixed(2) + 
                  '\nCosto + IVA: $' + costoConIVA.toFixed(2) + 
                  '\nGanancia: $' + ganancia.toFixed(2) + 
                  '\nPrecio Final: $' + precio.toFixed(2));
            cerrarModalEditarProducto();
            cargarProductos();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error al actualizar producto:', error);
        alert('❌ Error al actualizar producto');
    }
});

async function desactivarProducto(productoId) {
    if (!confirm('¿Desactivar este producto? No aparecerá en el sistema de ventas.')) {
        return;
    }
    
    try {
        const response = await fetch(`/gerente/api/productos/${productoId}/desactivar`, {
            method: 'PUT'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Producto desactivado exitosamente');
            cargarProductos();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error al desactivar producto:', error);
        alert('❌ Error al desactivar producto');
    }
}

async function activarProducto(productoId) {
    try {
        const response = await fetch(`/gerente/api/productos/${productoId}/activar`, {
            method: 'PUT'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Producto activado exitosamente');
            cargarProductos();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error al activar producto:', error);
        alert('❌ Error al activar producto');
    }
}

function cerrarModalEditarProducto() {
    document.getElementById('modal-editar-producto').style.display = 'none';
}

// Cerrar modales al hacer clic fuera
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};


// ==================== GESTIÓN DE DESCUENTOS ====================

async function cargarDescuentos() {
    try {
        const response = await fetch('/gerente/api/descuentos');
        const data = await response.json();
        
        if (data.success) {
            mostrarDescuentosGerente(data.descuentos);
        } else {
            alert('Error al cargar descuentos: ' + data.message);
        }
    } catch (error) {
        console.error('Error al cargar descuentos:', error);
        alert('Error al cargar descuentos');
    }
}

function mostrarDescuentosGerente(descuentos) {
    const tbody = document.querySelector('#tabla-descuentos-gerente tbody');
    tbody.innerHTML = '';
    
    if (descuentos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">No hay descuentos registrados</td></tr>';
        return;
    }
    
    descuentos.forEach(desc => {
        const row = document.createElement('tr');
        const estado = desc.activo ? 
            '<span class="badge badge-success">Activo</span>' : 
            '<span class="badge badge-secondary">Inactivo</span>';
        
        const fechaFin = desc.fecha_fin ? 
            new Date(desc.fecha_fin).toLocaleDateString('es-MX') : 
            'Sin límite';
        
        const tipoDescuento = desc.cliente_id ? 
            '' : 
            '<span class="badge badge-warning" style="margin-left: 5px;">General</span>';
        
        row.innerHTML = `
            <td>${desc.cliente_nombre}${tipoDescuento}</td>
            <td>${desc.cliente_correo}</td>
            <td style="font-weight: bold; color: #28a745;">${desc.porcentaje_descuento}%</td>
            <td>${new Date(desc.fecha_inicio).toLocaleDateString('es-MX')}</td>
            <td>${fechaFin}</td>
            <td>${estado}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="eliminarDescuentoGerente(${desc.id})">
                    🗑️ Eliminar
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function mostrarModalDescuentoGerente() {
    try {
        const response = await fetch('/gerente/api/clientes');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('descuento-cliente-gerente');
            select.innerHTML = '<option value="">Descuento general (sin cliente específico)</option>';
            
            data.clientes.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.id;
                option.textContent = `${cliente.nombre} (${cliente.correo})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error al cargar clientes:', error);
    }
    
    document.getElementById('form-descuento-gerente').reset();
    document.getElementById('modal-descuento-titulo').textContent = 'Nuevo Descuento';
    document.getElementById('modal-descuento-gerente').style.display = 'block';
}

function cerrarModalDescuentoGerente() {
    document.getElementById('modal-descuento-gerente').style.display = 'none';
}

// Manejar envío del formulario de descuento
document.getElementById('form-descuento-gerente')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const clienteId = document.getElementById('descuento-cliente-gerente').value;
    const porcentaje = document.getElementById('descuento-porcentaje-gerente').value;
    const fechaFin = document.getElementById('descuento-fecha-fin-gerente').value || null;
    const notas = document.getElementById('descuento-notas-gerente').value || null;
    
    if (!porcentaje) {
        alert('Por favor ingrese el porcentaje de descuento');
        return;
    }
    
    try {
        const response = await fetch('/gerente/api/descuentos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cliente_id: clienteId ? parseInt(clienteId) : null,
                porcentaje_descuento: parseFloat(porcentaje),
                fecha_fin: fechaFin,
                notas: notas
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Descuento creado exitosamente');
            cerrarModalDescuentoGerente();
            cargarDescuentos();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error al crear descuento:', error);
        alert('❌ Error al crear descuento');
    }
});

async function eliminarDescuentoGerente(descuentoId) {
    if (!confirm('¿Está seguro de eliminar este descuento?')) {
        return;
    }
    
    try {
        const response = await fetch(`/gerente/api/descuentos/${descuentoId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Descuento eliminado exitosamente');
            cargarDescuentos();
        } else {
            alert('❌ Error al eliminar descuento');
        }
    } catch (error) {
        console.error('Error al eliminar descuento:', error);
        alert('❌ Error al eliminar descuento');
    }
}


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


// ==================== PUNTO DE VENTA ====================


function abrirCajeroGerente() {
    // Guardar en sessionStorage que el gerente está usando el cajero
    sessionStorage.setItem('gerente_usando_cajero', 'true');
    
    // Mostrar modal para configurar caja inicial
    document.getElementById('modal-caja-inicial-gerente').style.display = 'flex';
    document.getElementById('monto-caja-gerente').value = '';
    document.getElementById('monto-caja-gerente').focus();
}

function cerrarModalCajaGerente() {
    document.getElementById('modal-caja-inicial-gerente').style.display = 'none';
    // Limpiar el flag de sessionStorage si cancela
    sessionStorage.removeItem('gerente_usando_cajero');
}

async function confirmarCajaGerente() {
    const monto = document.getElementById('monto-caja-gerente').value;
    
    // Validar que se haya ingresado un monto
    if (!monto || monto === '') {
        alert('Por favor ingrese un monto');
        return;
    }
    
    // Convertir a número y validar monto mínimo
    const montoNumero = parseFloat(monto);
    
    if (isNaN(montoNumero)) {
        alert('Por favor ingrese un monto válido');
        return;
    }
    
    if (montoNumero < 200) {
        alert('El monto mínimo de caja es de $200.00');
        document.getElementById('monto-caja-gerente').focus();
        return;
    }
    
    try {
        const response = await fetch('/api/set-caja', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ monto: montoNumero })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirigir al cajero después de configurar la caja
            window.location.href = '/cajero';
        } else {
            alert('Error al configurar la caja: ' + data.message);
        }
    } catch (error) {
        console.error('Error al configurar la caja:', error);
        alert('Error al configurar la caja');
    }
}

// Permitir Enter para confirmar en el input de caja
document.getElementById('monto-caja-gerente')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        confirmarCajaGerente();
    }
});



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