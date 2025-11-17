let cart = [];
let ordenActualPago = null;
let clienteSeleccionado = null;
let todosLosClientes = [];
let descuentoDisponible = null;
let descuentoAplicado = false;
function filterCategory(categoria) {
    const products = document.querySelectorAll('.product-card');
    const buttons = document.querySelectorAll('.category-btn');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-category="${categoria}"]`).classList.add('active');
    
    products.forEach(product => {
        if (categoria === 'all' || product.dataset.categoria === categoria) {
            product.classList.remove('hidden');
        } else {
            product.classList.add('hidden');
        }
    });
}

function searchProducts() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const products = document.querySelectorAll('.product-card');
    
    products.forEach(product => {
        const name = product.querySelector('.product-name').textContent.toLowerCase();
        const description = product.querySelector('.product-description').textContent.toLowerCase();
        
        if (name.includes(searchTerm) || description.includes(searchTerm)) {
            product.classList.remove('hidden');
        } else {
            product.classList.add('hidden');
        }
    });
}

function addToCart(producto) {
    // Asegurar que precio y costo sean números
    producto.precio = parseFloat(producto.precio);
    producto.costo = parseFloat(producto.costo);
    
    const existingItem = cart.find(item => item.id === producto.id);
    
    if (existingItem) {
        existingItem.cantidad++;
    } else {
        cart.push({
            ...producto,
            cantidad: 1
        });
    }
    
    updateCart();
}

function updateCart() {
    const cartItemsDiv = document.getElementById('cart-items');
    const totalSpan = document.getElementById('total');
    
    if (cart.length === 0) {
        cartItemsDiv.innerHTML = '<p class="empty-cart">No hay productos</p>';
        totalSpan.textContent = '0.00';
        return;
    }
    
    let html = '';
    let total = 0;
    
    cart.forEach((item, index) => {
        const precio = parseFloat(item.precio);
        const cantidad = parseInt(item.cantidad);
        const subtotal = precio * cantidad;
        total += subtotal;
        
        html += `
            <div class="cart-item">
                <div class="cart-item-header">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${item.nombre}</div>
                        <div class="cart-item-details">$${precio.toFixed(2)} c/u</div>
                    </div>
                </div>
                <div class="cart-item-controls">
                    <button onclick="decreaseQuantity(${index})">-</button>
                    <span class="cart-item-quantity">${cantidad}</span>
                    <button onclick="increaseQuantity(${index})">+</button>
                    <button class="btn-remove" onclick="removeFromCart(${index})">×</button>
                </div>
                <div class="cart-item-subtotal">
                    Subtotal: $${subtotal.toFixed(2)}
                </div>
            </div>
        `;
    });
    
    cartItemsDiv.innerHTML = html;
    totalSpan.textContent = total.toFixed(2);
}

function increaseQuantity(index) {
    cart[index].cantidad++;
    updateCart();
}

function decreaseQuantity(index) {
    if (cart[index].cantidad > 1) {
        cart[index].cantidad--;
    } else {
        cart.splice(index, 1);
    }
    updateCart();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCart();
}

function limpiarOrden() {
    if (cart.length === 0) return;
    
    if (confirm('¿Limpiar la orden actual?')) {
        cart = [];
        updateCart();
    }
}

async function guardarOrden() {
    if (cart.length === 0) {
        alert('La orden está vacía');
        return;
    }
    
    const notas = document.getElementById('orden-notas').value.trim();
    
    try {
        const ordenData = {
            items: cart,
            notas: notas || null,
            cliente_id: clienteSeleccionado ? clienteSeleccionado.id : null
        };
        
        const response = await fetch('/api/crear-orden', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ordenData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Orden guardada exitosamente');
            cart = [];
            updateCart();
            
            // Limpiar notas y cliente
            document.getElementById('orden-notas').value = '';
            clienteSeleccionado = null;
            const clienteInfo = document.getElementById('cliente-seleccionado');
            clienteInfo.innerHTML = '<span class="cliente-nombre">Sin cliente</span>';
            clienteInfo.classList.remove('selected');
            
            loadOrdenes();
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Error al guardar la orden');
        console.error(error);
    }
}

async function loadOrdenes() {
    try {
        const response = await fetch('/api/ordenes');
        const data = await response.json();
        
        if (data.success) {
            displayOrdenes(data.ordenes);
            const pendientes = data.ordenes.filter(o => o.status === 'pendiente').length;
            document.getElementById('ordenes-count').textContent = pendientes;
        }
    } catch (error) {
        console.error('Error al cargar órdenes:', error);
    }
}

function displayOrdenes(ordenes) {
    const ordenesListDiv = document.getElementById('ordenes-list');
    
    if (!ordenes || ordenes.length === 0) {
        ordenesListDiv.innerHTML = '<p class="empty-ordenes">No hay órdenes activas</p>';
        return;
    }
    
    let html = '';
    
    ordenes.forEach(orden => {
        // Asegurar que items sea un array
        const items = Array.isArray(orden.items) ? orden.items : [];
        const total = parseFloat(orden.total || 0);
        const status = orden.status || 'pendiente';
        const ordenId = orden.orden_id || '';
        const cajero = orden.cajero || 'N/A';
        const fecha = orden.fecha || '';
        const clienteNombre = orden.cliente_nombre || 'Sin cliente';
        
        html += `
            <div class="orden-card ${status}">
                <div class="orden-header">
                    <span class="orden-id">Orden: ${ordenId.substring(0, 8)}</span>
                    <span class="orden-status ${status}">${status.toUpperCase()}</span>
                </div>
                <div class="orden-info">
                    <div class="orden-cajero">Cajero: ${cajero}</div>
                    <div class="orden-cliente">Cliente: ${clienteNombre}</div>
                    <div class="orden-fecha">${fecha}</div>
                </div>
                <div class="orden-items">
                    ${items.length > 0 ? items.map(item => {
                        const precio = parseFloat(item.precio || 0);
                        const cantidad = parseInt(item.cantidad || 0);
                        const subtotal = precio * cantidad;
                        
                        return `
                            <div class="orden-item">
                                <div>
                                    <div class="orden-item-name">${item.nombre || 'Producto'}</div>
                                    <div class="orden-item-quantity">Cantidad: ${cantidad}</div>
                                </div>
                                <div class="orden-item-price">$${subtotal.toFixed(2)}</div>
                            </div>
                        `;
                    }).join('') : '<p style="text-align: center; color: #999;">Sin productos</p>'}
                </div>
                <div class="orden-footer">
                    <div class="orden-total">Total: $${total.toFixed(2)}</div>
                    <div class="orden-actions">
                        ${status === 'pendiente' ? `
                            <button class="btn-pagar" onclick="pagarOrden('${ordenId}')">Pagar</button>
                            <button class="btn-cancelar" onclick="cancelarOrden('${ordenId}')">Cancelar</button>
                        ` : '<button class="btn-pagar" disabled>Pagada</button>'}
                    </div>
                </div>
            </div>
        `;
    });
    
    ordenesListDiv.innerHTML = html;
}


async function pagarOrden(ordenId) {
    try {
        const response = await fetch(`/api/orden/${ordenId}`);
        const data = await response.json();
        
        if (data.success) {
            ordenActualPago = data.orden;
            
            // Si la orden tiene cliente_id, cargar los datos del cliente
            if (data.orden.cliente_id) {
                await cargarClienteParaPago(data.orden.cliente_id);
            } else {
                clienteSeleccionado = null;
            }
            
            abrirModalPago(data.orden);
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Error al cargar la orden');
        console.error(error);
    }
}

async function cargarClienteParaPago(clienteId) {
    try {
        const response = await fetch(`/api/cliente/${clienteId}`);
        const data = await response.json();
        
        if (data.success) {
            clienteSeleccionado = data.cliente;
        }
    } catch (error) {
        console.error('Error al cargar cliente:', error);
        clienteSeleccionado = null;
    }
}

async function abrirModalPago(orden) {
    const modal = document.getElementById('pago-modal');
    const totalSpan = document.getElementById('pago-total');
    const pagoInput = document.getElementById('pago-con-input');
    const cambioContainer = document.getElementById('pago-cambio-container');
    const errorDiv = document.getElementById('pago-error');
    
    // Reset de variables de descuento
    descuentoDisponible = null;
    descuentoAplicado = false;
    
    // Verificar si hay descuento disponible (pero NO aplicarlo automáticamente)
    if (orden.cliente_id || clienteSeleccionado) {
        const clienteId = orden.cliente_id || (clienteSeleccionado ? clienteSeleccionado.id : null);
        descuentoDisponible = await verificarDescuentoCliente(clienteId);
    }
    
    // Guardar el total original sin descuento
    ordenActualPago.total_original = parseFloat(orden.total);
    ordenActualPago.total = parseFloat(orden.total);
    
    // Resetear modal
    totalSpan.textContent = `${ordenActualPago.total.toFixed(2)}`;
    pagoInput.value = '';
    cambioContainer.style.display = 'none';
    errorDiv.style.display = 'none';
    
    // Mostrar información de descuento/puntos
    const puntosInfoDiv = document.getElementById('puntos-info');
    
    // Si hay cliente, mostrar opciones disponibles
    if (clienteSeleccionado && (orden.cliente_id || clienteSeleccionado.id)) {
        // Calcular puntos necesarios para pago con puntos
        const puntosNecesarios = calcularPuntosTotales(orden.items);
        const puntosCliente = clienteSeleccionado.puntos_acumulados || 0;
        const puedeUsarPuntos = puntosCliente >= puntosNecesarios;
        
        let htmlContent = `
            <div class="puntos-detalle">
                <div class="puntos-item">
                    <span class="puntos-label">👤 Cliente:</span>
                    <span class="puntos-value">${clienteSeleccionado.nombre}</span>
                </div>
        `;
        
        // Mostrar descuento disponible (SIN aplicarlo)
        if (descuentoDisponible) {
            const montoDescuento = (ordenActualPago.total_original * descuentoDisponible.porcentaje_descuento) / 100;
            const totalConDescuento = ordenActualPago.total_original - montoDescuento;
            
            htmlContent += `
                <div style="background: #fff3e0; border: 2px dashed #ff9800; border-radius: 8px; padding: 12px; margin: 10px 0;">
                    <div style="text-align: center; margin-bottom: 8px;">
                        <span style="font-size: 20px;">🎁</span>
                        <strong style="color: #e65100; display: block; margin-top: 5px;">¡Descuento Disponible!</strong>
                    </div>
                    <div style="font-size: 13px; color: #666; margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                            <span>Descuento:</span>
                            <strong style="color: #ff9800;">${descuentoDisponible.porcentaje_descuento}%</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                            <span>Ahorras:</span>
                            <strong style="color: #f44336;">${montoDescuento.toFixed(2)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 8px 0; padding-top: 8px; border-top: 1px solid #ddd;">
                            <span>Pagarías:</span>
                            <strong style="color: #2e7d32; font-size: 16px;">${totalConDescuento.toFixed(2)}</strong>
                        </div>
                    </div>
                    <button class="btn-aplicar-descuento" onclick="aplicarDescuento()" style="width: 100%; padding: 10px; background: #ff9800; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 8px;">
                        🎉 Aplicar Descuento
                    </button>
                </div>
            `;
        }
        
        // Mostrar información de puntos
        htmlContent += `
                <div class="puntos-item">
                    <span class="puntos-label">💎 Puntos disponibles:</span>
                    <span class="puntos-value ${puedeUsarPuntos ? 'suficiente' : 'insuficiente'}">${puntosCliente} pts</span>
                </div>
                <div class="puntos-item">
                    <span class="puntos-label">🎫 Puntos necesarios:</span>
                    <span class="puntos-value">${puntosNecesarios} pts</span>
                </div>
                ${puedeUsarPuntos ? `
                    <button class="btn-pagar-puntos" onclick="pagarConPuntos()">
                        💳 Pagar con Puntos
                    </button>
                ` : `
                    <div class="puntos-insuficientes">
                        ⚠️ Puntos insuficientes. Faltan ${puntosNecesarios - puntosCliente} puntos.
                    </div>
                `}
            </div>
        `;
        
        puntosInfoDiv.innerHTML = htmlContent;
        puntosInfoDiv.style.display = 'block';
    } else {
        puntosInfoDiv.innerHTML = `
            <div class="puntos-detalle">
                <div style="text-align: center; padding: 20px; color: #999;">
                    ℹ️ No hay cliente asociado a esta orden
                </div>
            </div>
        `;
        puntosInfoDiv.style.display = 'block';
    }
    
    modal.style.display = 'flex';
    
    // Focus en el input después de mostrar el modal
    setTimeout(() => pagoInput.focus(), 100);
}


async function verificarDescuentoCliente(clienteId) {
    if (!clienteId) return null;
    
    try {
        const response = await fetch(`/api/descuento-cliente/${clienteId}`);
        const data = await response.json();
        
        if (data.success && data.descuento) {
            return data.descuento;
        }
        return null;
    } catch (error) {
        console.error('Error al verificar descuento:', error);
        return null;
    }
}

// Nueva función para calcular puntos totales basado en precio_puntos
function calcularPuntosTotales(items) {
    let totalPuntos = 0;
    
    items.forEach(item => {
        const precioPuntos = parseInt(item.precio_puntos || 0);
        const cantidad = parseInt(item.cantidad || 0);
        totalPuntos += precioPuntos * cantidad;
    });
    
    return totalPuntos;
}


function cerrarModalPago() {
    const modal = document.getElementById('pago-modal');
    modal.style.display = 'none';
    ordenActualPago = null;
}

function setPagoCon(valor) {
    const pagoInput = document.getElementById('pago-con-input');
    
    if (valor === 'exacto') {
        pagoInput.value = parseFloat(ordenActualPago.total).toFixed(2);
    } else {
        pagoInput.value = valor.toFixed(2);
    }
    
    calcularCambio();
}

function calcularCambio() {
    if (!ordenActualPago) return;
    
    const pagoInput = document.getElementById('pago-con-input');
    const cambioContainer = document.getElementById('pago-cambio-container');
    const cambioValue = document.getElementById('pago-cambio');
    const errorDiv = document.getElementById('pago-error');
    const btnConfirmar = document.getElementById('btn-confirmar');
    
    const pagoCon = parseFloat(pagoInput.value) || 0;
    const total = parseFloat(ordenActualPago.total);
    
    errorDiv.style.display = 'none';
    
    if (pagoCon === 0) {
        cambioContainer.style.display = 'none';
        btnConfirmar.disabled = true;
        return;
    }
    
    if (pagoCon < total) {
        const faltante = total - pagoCon;
        errorDiv.textContent = `Pago insuficiente. Falta: $${faltante.toFixed(2)}`;
        errorDiv.style.display = 'block';
        cambioContainer.style.display = 'none';
        btnConfirmar.disabled = true;
    } else {
        const cambio = pagoCon - total;
        
        // NUEVA VALIDACIÓN: Verificar si hay suficiente cambio en caja
        if (cambio > 0) {
            verificarCambioDisponible(cambio, total).then(suficiente => {
                if (!suficiente) {
                    btnConfirmar.disabled = true;
                } else {
                    cambioValue.textContent = `$${cambio.toFixed(2)}`;
                    cambioContainer.style.display = 'block';
                    btnConfirmar.disabled = false;
                }
            });
        } else {
            // Pago exacto
            cambioValue.textContent = `$${cambio.toFixed(2)}`;
            cambioContainer.style.display = 'block';
            btnConfirmar.disabled = false;
        }
    }
}

async function verificarCambioDisponible(cambioNecesario, totalVenta) {
    try {
        const response = await fetch('/api/caja-actual');
        const data = await response.json();
        
        if (data.success) {
            const cajaActual = data.caja_actual;
            // La caja después de recibir el pago pero antes de dar cambio
            const cajaDespuesDePago = cajaActual + totalVenta;
            const cajaFinal = cajaDespuesDePago - cambioNecesario;
            
            const errorDiv = document.getElementById('pago-error');
            
            if (cajaFinal < 0) {
                errorDiv.textContent = `⚠️ No hay suficiente cambio en caja.\nCambio necesario: $${cambioNecesario.toFixed(2)}\nEfectivo disponible: $${cajaActual.toFixed(2)}\nSolicite al cliente un monto más cercano al total.`;
                errorDiv.style.display = 'block';
                return false;
            }
            
            return true;
        }
        return true; // Si hay error, permitir continuar
    } catch (error) {
        console.error('Error al verificar cambio:', error);
        return true; // Si hay error, permitir continuar
    }
}

async function confirmarPago() {
    if (!ordenActualPago) return;
    
    const pagoInput = document.getElementById('pago-con-input');
    const pagoCon = parseFloat(pagoInput.value);
    
    if (!pagoCon || pagoCon < ordenActualPago.total) {
        alert('El monto de pago es insuficiente');
        return;
    }
    
    const btnConfirmar = document.getElementById('btn-confirmar');
    btnConfirmar.disabled = true;
    btnConfirmar.textContent = 'Procesando...';
    
    try {
        // Preparar datos del pago
        const pagoData = {
            orden_id: ordenActualPago.orden_id,
            pago_con: pagoCon,
            cliente_id: ordenActualPago.cliente_id || null
        };
        
        // Si hay descuento APLICADO, incluirlo
        if (descuentoAplicado && ordenActualPago.descuento_id) {
            pagoData.descuento_id = ordenActualPago.descuento_id;
            pagoData.descuento_porcentaje = ordenActualPago.descuento_porcentaje;
            pagoData.total_original = ordenActualPago.total_original;
        }
        
        const response = await fetch('/api/procesar-pago', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(pagoData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            const cambio = data.cambio;
            let mensaje = 'Pago procesado exitosamente\n\n';
            
            // Si hubo descuento aplicado, mostrarlo
            if (data.descuento_aplicado) {
                mensaje += `🎉 DESCUENTO APLICADO 🎉\n`;
                mensaje += `Total Original: ${data.total_original.toFixed(2)}\n`;
                mensaje += `Descuento (${data.descuento_porcentaje}%): -${data.descuento_monto.toFixed(2)}\n`;
                mensaje += `━━━━━━━━━━━━━━━━━━━━\n`;
            }
            
            mensaje += `Total: ${ordenActualPago.total.toFixed(2)}\n`;
            mensaje += `Pagó con: ${pagoCon.toFixed(2)}\n`;
            
            if (cambio > 0) {
                mensaje += `Cambio: ${cambio.toFixed(2)}\n`;
            }
            
            if (data.puntos_ganados) {
                mensaje += `\nPuntos ganados: ${data.puntos_ganados} pts`;
            }
            
            alert(mensaje);
            
            // Descargar recibo PDF automáticamente
            descargarRecibo(data.venta_id);
            
            cerrarModalPago();
            loadOrdenes();
            
            // Actualizar puntos del cliente si existe
            if (clienteSeleccionado && data.puntos_nuevos) {
                clienteSeleccionado.puntos_acumulados = data.puntos_nuevos;
            }
            
            // Resetear variables de descuento
            descuentoDisponible = null;
            descuentoAplicado = false;
        } else {
            alert(data.message);
            btnConfirmar.disabled = false;
            btnConfirmar.textContent = 'Confirmar Pago';
        }
    } catch (error) {
        alert('Error al procesar el pago');
        console.error(error);
        btnConfirmar.disabled = false;
        btnConfirmar.textContent = 'Confirmar Pago';
    }
}

function descargarRecibo(ventaId) {
    // Crear un enlace temporal para descargar el PDF
    const link = document.createElement('a');
    link.href = `/api/generar-recibo/${ventaId}`;
    link.download = `recibo_${ventaId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function toggleOrdenes() {
    const modal = document.getElementById('ordenes-modal');
    if (modal.style.display === 'none') {
        modal.style.display = 'flex';
        loadOrdenes();
    } else {
        modal.style.display = 'none';
    }
}

// Modificar función de logout para manejar gerentes
async function logout() {
    const esGerenteUsandoCajero = sessionStorage.getItem('gerente_usando_cajero') === 'true';
    
    let mensaje = '¿Desea cerrar sesión?';
    if (esGerenteUsandoCajero) {
        mensaje = '¿Desea cerrar sesión?\n\n⚠️ Se cerrará su sesión y se perderán los datos de caja si no ha hecho cierre.\n\n';
    } else {
        mensaje = '¿Desea cerrar sesión?\n\nSe eliminará toda la información de la sesión actual.';
    }
    
    if (!confirm(mensaje)) {
        return;
    }
    
    // Limpiar sessionStorage
    sessionStorage.removeItem('gerente_usando_cajero');
    
    try {
        const response = await fetch('/api/cerrar-sesion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/';
        } else {
            alert('Error al cerrar sesión: ' + data.message);
        }
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
        window.location.href = '/';
    }
}
async function abrirCierreCaja() {
    // Primero verificar si hay órdenes pendientes
    try {
        const responseOrdenes = await fetch('/api/ordenes');
        const dataOrdenes = await responseOrdenes.json();
        
        if (dataOrdenes.success) {
            const ordenesPendientes = dataOrdenes.ordenes.filter(o => o.status === 'pendiente');
            
            if (ordenesPendientes.length > 0) {
                alert(`⚠️ NO SE PUEDE CERRAR CAJA\n\nTiene ${ordenesPendientes.length} orden(es) pendiente(s) de pago.\n\nPor favor complete o cancele todas las órdenes antes de realizar el cierre de caja.`);
                return;
            }
        }
    } catch (error) {
        console.error('Error al verificar órdenes:', error);
        alert('Error al verificar órdenes pendientes');
        return;
    }
    
    const modal = document.getElementById('cierre-caja-modal');
    const loadingDiv = document.getElementById('cierre-loading');
    const contentDiv = document.getElementById('cierre-content');
    
    modal.style.display = 'flex';
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/resumen-caja');
        const data = await response.json();
        
        if (data.success) {
            mostrarResumenCaja(data.resumen);
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
        } else {
            alert(data.message);
            cerrarCierreCaja();
        }
    } catch (error) {
        alert('Error al cargar información de caja');
        console.error(error);
        cerrarCierreCaja();
    }
}

function mostrarResumenCaja(resumen) {
    // Información general
    document.getElementById('cierre-cajero').textContent = resumen.cajero;
    
    const fechaInicio = new Date(resumen.fecha_inicio);
    document.getElementById('cierre-fecha-inicio').textContent = 
        fechaInicio.toLocaleString('es-MX', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    
    // Resumen financiero
    document.getElementById('cierre-monto-inicial').textContent = 
        `$${parseFloat(resumen.monto_inicial).toFixed(2)}`;
    document.getElementById('cierre-total-ventas').textContent = 
        `$${parseFloat(resumen.total_ventas).toFixed(2)}`;
    document.getElementById('cierre-cantidad-ordenes').textContent = 
        resumen.cantidad_ordenes;
    document.getElementById('cierre-monto-final').textContent = 
        `$${parseFloat(resumen.monto_actual).toFixed(2)}`;
    
    // Detalle de ventas
    const ventasDetalleDiv = document.getElementById('ventas-detalle-list');
    
    if (resumen.ventas && resumen.ventas.length > 0) {
        let html = '';
        resumen.ventas.forEach(venta => {
            const fecha = new Date(venta.fecha_venta);
            const hora = fecha.toLocaleTimeString('es-MX', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            html += `
                <div class="venta-item">
                    <div class="venta-item-info">
                        <div class="venta-orden">Orden: ${venta.orden_id.substring(0, 8).toUpperCase()}</div>
                        <div class="venta-hora">${hora}</div>
                    </div>
                    <div class="venta-monto">$${parseFloat(venta.total).toFixed(2)}</div>
                </div>
            `;
        });
        ventasDetalleDiv.innerHTML = html;
    } else {
        ventasDetalleDiv.innerHTML = '<p class="no-ventas">No hay ventas registradas</p>';
    }
}

function cerrarCierreCaja() {
    const modal = document.getElementById('cierre-caja-modal');
    modal.style.display = 'none';
}

async function confirmarCierreCaja() {
    // Verificar nuevamente antes de confirmar
    try {
        const responseOrdenes = await fetch('/api/ordenes');
        const dataOrdenes = await responseOrdenes.json();
        
        if (dataOrdenes.success) {
            const ordenesPendientes = dataOrdenes.ordenes.filter(o => o.status === 'pendiente');
            
            if (ordenesPendientes.length > 0) {
                alert(`⚠️ NO SE PUEDE CERRAR CAJA\n\nSe detectaron ${ordenesPendientes.length} orden(es) pendiente(s).\n\nPor favor complete o cancele todas las órdenes antes de continuar.`);
                cerrarCierreCaja();
                return;
            }
        }
    } catch (error) {
        console.error('Error al verificar órdenes:', error);
        alert('Error al verificar órdenes pendientes');
        return;
    }
    
    if (!confirm('¿Está seguro de realizar el cierre de caja?\n\nEsta acción guardará el registro del cierre.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/cerrar-caja', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ CIERRE DE CAJA EXITOSO\n\nEl registro se ha guardado correctamente.\n\nPuede continuar trabajando normalmente.');
            cerrarCierreCaja();
        } else {
            alert('❌ ERROR\n\n' + data.message);
        }
    } catch (error) {
        alert('❌ Error al realizar el cierre de caja');
        console.error(error);
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    updateCart();
    loadOrdenes();
    
    // Actualizar órdenes cada 30 segundos
    setInterval(loadOrdenes, 30000);
});

// Nueva función para regresar al menú de gerente
function regresarMenuGerente() {
    if (cart.length > 0) {
        if (!confirm('⚠️ Tiene productos en la orden actual.\n\n¿Desea salir de todos modos? Los productos se perderán.')) {
            return;
        }
    }
    
    // NO limpiar sessionStorage, mantener el flag
    // NO limpiar Redis, mantener la sesión de caja
    
    // Redirigir al dashboard de gerente
    window.location.href = '/gerente/dashboard';
}

// Funciones para manejo de clientes
async function abrirModalClientes() {
    const modal = document.getElementById('clientes-modal');
    modal.style.display = 'flex';
    
    await cargarClientes();
}

function cerrarModalClientes() {
    const modal = document.getElementById('clientes-modal');
    modal.style.display = 'none';
    ocultarFormularioCliente();
}

async function cargarClientes() {
    const listaDiv = document.getElementById('clientes-lista');
    listaDiv.innerHTML = '<p class="loading-clientes">Cargando clientes...</p>';
    
    try {
        const response = await fetch('/api/clientes');
        const data = await response.json();
        
        if (data.success) {
            todosLosClientes = data.clientes;
            mostrarClientes(todosLosClientes);
        } else {
            listaDiv.innerHTML = '<p class="empty-clientes">Error al cargar clientes</p>';
        }
    } catch (error) {
        console.error('Error al cargar clientes:', error);
        listaDiv.innerHTML = '<p class="empty-clientes">Error al cargar clientes</p>';
    }
}

function mostrarClientes(clientes) {
    const listaDiv = document.getElementById('clientes-lista');
    
    if (!clientes || clientes.length === 0) {
        listaDiv.innerHTML = '<p class="empty-clientes">No hay clientes registrados</p>';
        return;
    }
    
    let html = '';
    clientes.forEach(cliente => {
        html += `
            <div class="cliente-card" onclick='seleccionarCliente(${JSON.stringify(cliente)})'>
                <div class="cliente-card-nombre">${cliente.nombre}</div>
                <div class="cliente-card-correo">${cliente.correo}</div>
                <div class="cliente-card-puntos">Puntos: ${cliente.puntos_acumulados || 0}</div>
            </div>
        `;
    });
    
    listaDiv.innerHTML = html;
}

function filtrarClientes() {
    const busqueda = document.getElementById('buscar-cliente-input').value.toLowerCase();
    
    if (!busqueda) {
        mostrarClientes(todosLosClientes);
        return;
    }
    
    const clientesFiltrados = todosLosClientes.filter(cliente => 
        cliente.correo.toLowerCase().includes(busqueda) ||
        cliente.nombre.toLowerCase().includes(busqueda)
    );
    
    mostrarClientes(clientesFiltrados);
}

function seleccionarCliente(cliente) {
    clienteSeleccionado = cliente;
    
    const clienteInfo = document.getElementById('cliente-seleccionado');
    clienteInfo.innerHTML = `
        <span class="cliente-nombre">${cliente.nombre}</span>
        <span class="cliente-correo">${cliente.correo}</span>
        <span class="cliente-puntos">Puntos: ${cliente.puntos_acumulados || 0}</span>
        <button class="btn-deseleccionar-cliente" onclick="event.stopPropagation(); deseleccionarCliente()">X</button>
    `;
    clienteInfo.classList.add('selected');
    
    cerrarModalClientes();
}

function deseleccionarCliente() {
    clienteSeleccionado = null;
    const clienteInfo = document.getElementById('cliente-seleccionado');
    clienteInfo.innerHTML = '<span class="cliente-nombre">Sin cliente</span>';
    clienteInfo.classList.remove('selected');
}

function mostrarFormularioCliente() {
    const formulario = document.getElementById('formulario-nuevo-cliente');
    formulario.style.display = 'block';
    document.getElementById('nuevo-cliente-nombre').focus();
}

function ocultarFormularioCliente() {
    const formulario = document.getElementById('formulario-nuevo-cliente');
    formulario.style.display = 'none';
    document.getElementById('nuevo-cliente-nombre').value = '';
    document.getElementById('nuevo-cliente-correo').value = '';
}

async function guardarNuevoCliente() {
    const nombre = document.getElementById('nuevo-cliente-nombre').value.trim();
    const correo = document.getElementById('nuevo-cliente-correo').value.trim();
    
    if (!nombre || !correo) {
        alert('Por favor complete todos los campos');
        return;
    }
    
    // Validar formato de correo
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(correo)) {
        alert('Por favor ingrese un correo válido');
        return;
    }
    
    try {
        const response = await fetch('/api/crear-cliente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nombre, correo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Cliente registrado exitosamente');
            ocultarFormularioCliente();
            await cargarClientes();
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Error al registrar cliente');
        console.error(error);
    }
}

function aplicarDescuento() {
    if (!descuentoDisponible || descuentoAplicado) return;
    
    const totalOriginal = ordenActualPago.total_original;
    const montoDescuento = (totalOriginal * descuentoDisponible.porcentaje_descuento) / 100;
    const totalConDescuento = totalOriginal - montoDescuento;
    
    // Aplicar descuento
    ordenActualPago.total = totalConDescuento;
    ordenActualPago.descuento_id = descuentoDisponible.id;
    ordenActualPago.descuento_porcentaje = descuentoDisponible.porcentaje_descuento;
    ordenActualPago.descuento_monto = montoDescuento;
    descuentoAplicado = true;
    
    // Actualizar el total mostrado
    document.getElementById('pago-total').textContent = `${totalConDescuento.toFixed(2)}`;
    
    // Actualizar la interfaz para mostrar que el descuento está aplicado
    const puntosInfoDiv = document.getElementById('puntos-info');
    
    let htmlContent = `
        <div class="puntos-detalle">
            <div class="puntos-item">
                <span class="puntos-label">👤 Cliente:</span>
                <span class="puntos-value">${clienteSeleccionado ? clienteSeleccionado.nombre : 'N/A'}</span>
            </div>
            <div style="background: #e8f5e9; border: 2px solid #4caf50; border-radius: 8px; padding: 12px; margin: 10px 0;">
                <div style="text-align: center; margin-bottom: 8px;">
                    <span style="font-size: 20px;">✅</span>
                    <strong style="color: #2e7d32; display: block; margin-top: 5px;">¡Descuento Aplicado!</strong>
                </div>
                <div style="font-size: 13px; color: #666; margin: 8px 0;">
                    <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                        <span>Total Original:</span>
                        <span style="text-decoration: line-through;">${totalOriginal.toFixed(2)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                        <span>Descuento (${descuentoDisponible.porcentaje_descuento}%):</span>
                        <strong style="color: #f44336;">-${montoDescuento.toFixed(2)}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 8px 0; padding-top: 8px; border-top: 2px solid #4caf50;">
                        <span style="font-weight: bold;">Total a Pagar:</span>
                        <strong style="color: #2e7d32; font-size: 16px;">${totalConDescuento.toFixed(2)}</strong>
                    </div>
                </div>
                <button class="btn-cancelar-descuento" onclick="cancelarDescuento()" style="width: 100%; padding: 8px; background: #f44336; color: white; border: none; border-radius: 6px; cursor: pointer; margin-top: 8px;">
                    ❌ Cancelar Descuento
                </button>
                <div style="background: #fff3cd; border-radius: 4px; padding: 6px; margin-top: 8px; text-align: center; color: #856404; font-size: 11px;">
                    ⚠️ Este descuento se eliminará después del pago
                </div>
            </div>
    `;
    
    // Agregar información de puntos si es necesario
    if (clienteSeleccionado) {
        const puntosNecesarios = calcularPuntosTotales(ordenActualPago.items);
        const puntosCliente = clienteSeleccionado.puntos_acumulados || 0;
        const puedeUsarPuntos = puntosCliente >= puntosNecesarios;
        
        htmlContent += `
            <div class="puntos-item" style="margin-top: 10px;">
                <span class="puntos-label">💎 Puntos disponibles:</span>
                <span class="puntos-value ${puedeUsarPuntos ? 'suficiente' : 'insuficiente'}">${puntosCliente} pts</span>
            </div>
            <div class="puntos-item">
                <span class="puntos-label">🎫 Puntos necesarios:</span>
                <span class="puntos-value">${puntosNecesarios} pts</span>
            </div>
        `;
    }
    
    htmlContent += `</div>`;
    
    puntosInfoDiv.innerHTML = htmlContent;
    
    // Limpiar campos de pago y recalcular
    document.getElementById('pago-con-input').value = '';
    document.getElementById('pago-cambio-container').style.display = 'none';
    document.getElementById('pago-error').style.display = 'none';
}

function cancelarDescuento() {
    if (!descuentoAplicado) return;
    
    // Restaurar total original
    ordenActualPago.total = ordenActualPago.total_original;
    delete ordenActualPago.descuento_id;
    delete ordenActualPago.descuento_porcentaje;
    delete ordenActualPago.descuento_monto;
    descuentoAplicado = false;
    
    // Actualizar el total mostrado
    document.getElementById('pago-total').textContent = `${ordenActualPago.total_original.toFixed(2)}`;
    
    // Volver a mostrar el botón de aplicar descuento
    const puntosInfoDiv = document.getElementById('puntos-info');
    const montoDescuento = (ordenActualPago.total_original * descuentoDisponible.porcentaje_descuento) / 100;
    const totalConDescuento = ordenActualPago.total_original - montoDescuento;
    
    let htmlContent = `
        <div class="puntos-detalle">
            <div class="puntos-item">
                <span class="puntos-label">👤 Cliente:</span>
                <span class="puntos-value">${clienteSeleccionado ? clienteSeleccionado.nombre : 'N/A'}</span>
            </div>
            <div style="background: #fff3e0; border: 2px dashed #ff9800; border-radius: 8px; padding: 12px; margin: 10px 0;">
                <div style="text-align: center; margin-bottom: 8px;">
                    <span style="font-size: 20px;">🎁</span>
                    <strong style="color: #e65100; display: block; margin-top: 5px;">¡Descuento Disponible!</strong>
                </div>
                <div style="font-size: 13px; color: #666; margin: 8px 0;">
                    <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                        <span>Descuento:</span>
                        <strong style="color: #ff9800;">${descuentoDisponible.porcentaje_descuento}%</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                        <span>Ahorras:</span>
                        <strong style="color: #f44336;">${montoDescuento.toFixed(2)}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 8px 0; padding-top: 8px; border-top: 1px solid #ddd;">
                        <span>Pagarías:</span>
                        <strong style="color: #2e7d32; font-size: 16px;">${totalConDescuento.toFixed(2)}</strong>
                    </div>
                </div>
                <button class="btn-aplicar-descuento" onclick="aplicarDescuento()" style="width: 100%; padding: 10px; background: #ff9800; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 8px;">
                    🎉 Aplicar Descuento
                </button>
            </div>
    `;
    
    // Agregar información de puntos
    if (clienteSeleccionado) {
        const puntosNecesarios = calcularPuntosTotales(ordenActualPago.items);
        const puntosCliente = clienteSeleccionado.puntos_acumulados || 0;
        const puedeUsarPuntos = puntosCliente >= puntosNecesarios;
        
        htmlContent += `
            <div class="puntos-item">
                <span class="puntos-label">💎 Puntos disponibles:</span>
                <span class="puntos-value ${puedeUsarPuntos ? 'suficiente' : 'insuficiente'}">${puntosCliente} pts</span>
            </div>
            <div class="puntos-item">
                <span class="puntos-label">🎫 Puntos necesarios:</span>
                <span class="puntos-value">${puntosNecesarios} pts</span>
            </div>
            ${puedeUsarPuntos ? `
                <button class="btn-pagar-puntos" onclick="pagarConPuntos()">
                    💳 Pagar con Puntos
                </button>
            ` : `
                <div class="puntos-insuficientes">
                    ⚠️ Puntos insuficientes. Faltan ${puntosNecesarios - puntosCliente} puntos.
                </div>
            `}
        `;
    }
    
    htmlContent += `</div>`;
    
    puntosInfoDiv.innerHTML = htmlContent;
    
    // Limpiar campos de pago y recalcular
    document.getElementById('pago-con-input').value = '';
    document.getElementById('pago-cambio-container').style.display = 'none';
    document.getElementById('pago-error').style.display = 'none';
}



async function pagarConPuntos() {
    if (!ordenActualPago || !clienteSeleccionado) return;
    
    // Calcular puntos necesarios usando precio_puntos
    const puntosNecesarios = calcularPuntosTotales(ordenActualPago.items);
    const puntosCliente = clienteSeleccionado.puntos_acumulados || 0;
    
    if (puntosCliente < puntosNecesarios) {
        alert('Puntos insuficientes para realizar el pago');
        return;
    }
    
    // Mostrar detalle de productos y puntos
    let detalleProductos = '\n📦 PRODUCTOS:\n';
    ordenActualPago.items.forEach(item => {
        const precioPuntos = parseInt(item.precio_puntos || 0);
        const cantidad = parseInt(item.cantidad || 1);
        const subtotalPuntos = precioPuntos * cantidad;
        detalleProductos += `\n• ${item.nombre} (x${cantidad})\n  ${precioPuntos} pts c/u = ${subtotalPuntos} pts`;
    });
    
    if (!confirm(`¿Confirmar pago con puntos?\n\n💰 Total en efectivo: $${ordenActualPago.total.toFixed(2)}\n${detalleProductos}\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n🎫 Total en puntos: ${puntosNecesarios} pts\n💎 Puntos actuales: ${puntosCliente} pts\n⭐ Puntos restantes: ${puntosCliente - puntosNecesarios} pts`)) {
        return;
    }
    
    // Deshabilitar botón para evitar doble click
    const btnPagarPuntos = event.target;
    btnPagarPuntos.disabled = true;
    btnPagarPuntos.textContent = '💳 Procesando...';
    
    try {
        const response = await fetch('/api/procesar-pago-puntos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orden_id: ordenActualPago.orden_id,
                cliente_id: clienteSeleccionado.id,
                puntos_necesarios: puntosNecesarios
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Mensaje más visual y detallado
            let mensaje = '✅ PAGO CON PUNTOS EXITOSO\n\n';
            mensaje += `━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
            mensaje += `💰 Valor en efectivo: $${ordenActualPago.total.toFixed(2)}\n\n`;
            mensaje += `🎫 Puntos usados: ${data.puntos_usados} pts\n`;
            mensaje += `⭐ Puntos restantes: ${data.puntos_restantes} pts\n\n`;
            mensaje += `━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
            mensaje += `Cliente: ${clienteSeleccionado.nombre}\n`;
            mensaje += `${clienteSeleccionado.correo}`;
            
            alert(mensaje);
            
            // Descargar recibo PDF automáticamente
            descargarRecibo(data.venta_id);
            
            // Actualizar puntos del cliente seleccionado
            clienteSeleccionado.puntos_acumulados = data.puntos_restantes;
            
            // Actualizar la información del cliente en la interfaz
            const clienteInfo = document.getElementById('cliente-seleccionado');
            if (clienteInfo.classList.contains('selected')) {
                clienteInfo.innerHTML = `
                    <span class="cliente-nombre">${clienteSeleccionado.nombre}</span>
                    <span class="cliente-correo">${clienteSeleccionado.correo}</span>
                    <span class="cliente-puntos">Puntos: ${clienteSeleccionado.puntos_acumulados}</span>
                    <button class="btn-deseleccionar-cliente" onclick="event.stopPropagation(); deseleccionarCliente()">X</button>
                `;
            }
            
            cerrarModalPago();
            loadOrdenes();
        } else {
            alert('❌ ERROR\n\n' + data.message);
            btnPagarPuntos.disabled = false;
            btnPagarPuntos.textContent = '💳 Pagar con Puntos';
        }
    } catch (error) {
        alert('❌ Error al procesar el pago con puntos\n\nIntente nuevamente.');
        console.error(error);
        btnPagarPuntos.disabled = false;
        btnPagarPuntos.textContent = '💳 Pagar con Puntos';
    }
}



async function cancelarOrden(ordenId) {
    if (!confirm('¿Está seguro de cancelar esta orden?\n\nEsta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/cancelar-orden/${ordenId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Orden cancelada exitosamente');
            loadOrdenes();
        } else {
            alert('❌ Error: ' + data.message);
        }
    } catch (error) {
        alert('❌ Error al cancelar la orden');
        console.error(error);
    }
}

