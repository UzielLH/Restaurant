// Variables globales
let reportesData = [];
let chartInstance = null;

// Navegación entre secciones
document.addEventListener('DOMContentLoaded', function() {
    // Configurar navegación
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            mostrarSeccion(section);
        });
    });
    
    // Cargar datos iniciales de reportes
    cargarReportesEmpleados();
    
    // Configurar fechas por defecto (últimos 30 días)
    const fechaFin = new Date();
    const fechaInicio = new Date();
    fechaInicio.setDate(fechaInicio.getDate() - 30);
    
    document.getElementById('fecha-inicio-reporte').valueAsDate = fechaInicio;
    document.getElementById('fecha-fin-reporte').valueAsDate = fechaFin;
});

function mostrarSeccion(seccionId) {
    // Ocultar todas las secciones
    const secciones = document.querySelectorAll('.content-section');
    secciones.forEach(seccion => {
        seccion.classList.remove('active');
    });
    
    // Mostrar sección seleccionada
    const seccionActiva = document.getElementById(seccionId);
    if (seccionActiva) {
        seccionActiva.classList.add('active');
    }
    
    // Actualizar navegación
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === seccionId) {
            item.classList.add('active');
        }
    });
    
    // Cargar datos específicos de la sección
    if (seccionId === 'reportes') {
        cargarReportesEmpleados();
    } else if (seccionId === 'clientes') {
        cargarClientes();
    } else if (seccionId === 'productos') {
        cargarProductos();
    } else if (seccionId === 'categorias') {
        cargarCategorias();
    } else if (seccionId === 'perfiles') {
        cargarPerfiles();
    }
}

// ===== REPORTES FINANCIEROS =====
async function generarReporte() {
    const fechaInicio = document.getElementById('fecha-inicio-reporte').value;
    const fechaFin = document.getElementById('fecha-fin-reporte').value;
    
    if (!fechaInicio || !fechaFin) {
        alert('Por favor seleccione ambas fechas');
        return;
    }
    
    await cargarReportesEmpleados(fechaInicio, fechaFin);
}

async function cargarReportesEmpleados(fechaInicio = null, fechaFin = null) {
    try {
        let url = '/admin/api/reportes-empleados';
        
        if (fechaInicio && fechaFin) {
            url += `?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            reportesData = data.reportes;
            mostrarResumenReportes(reportesData);
            mostrarGraficaEmpleados(reportesData);
        } else {
            alert('Error al cargar reportes: ' + data.message);
        }
    } catch (error) {
        console.error('Error al cargar reportes:', error);
        alert('Error al cargar reportes');
    }
}

function mostrarResumenReportes(reportes) {
    // Calcular totales
    const totalOrdenes = reportes.reduce((sum, r) => sum + r.cantidad_ordenes, 0);
    const totalIngresos = reportes.reduce((sum, r) => sum + r.ingresos_totales, 0);
    const totalCostos = reportes.reduce((sum, r) => sum + r.costos_totales, 0);
    const totalGanancias = reportes.reduce((sum, r) => sum + r.ganancias_netas, 0);
    
    // Actualizar tarjetas
    document.getElementById('ordenes-totales').textContent = totalOrdenes.toLocaleString();
    document.getElementById('ingresos-totales').textContent = `$${totalIngresos.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('inversion-total').textContent = `$${totalCostos.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('ganancias-netas').textContent = `$${totalGanancias.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    // Actualizar tabla de detalle
    const tbody = document.querySelector('#tabla-ventas-reporte tbody');
    tbody.innerHTML = '';
    
    if (reportes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #999;">No hay datos para mostrar</td></tr>';
        return;
    }
    
    reportes.forEach(reporte => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>-</td>
            <td>${reporte.empleado_id}</td>
            <td>${reporte.empleado_nombre}</td>
            <td>$${reporte.ingresos_totales.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td>$${reporte.costos_totales.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td style="color: #28a745; font-weight: bold;">$${reporte.ganancias_netas.toLocaleString('es-MX', {minimumFractionDigits: 2})}</td>
            <td>${reporte.cantidad_ordenes} órdenes</td>
        `;
        tbody.appendChild(row);
    });
}

function mostrarGraficaEmpleados(reportes) {
    const container = document.querySelector('.report-table-card');
    
    // Verificar si ya existe el canvas, si no, crearlo
    let canvas = document.getElementById('grafica-empleados');
    if (!canvas) {
        const chartContainer = document.createElement('div');
        chartContainer.style.marginTop = '30px';
        chartContainer.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3>Desempeño por Empleado</h3>
                <button class="btn btn-primary" onclick="exportarReportePDF()">
                    📄 Exportar a PDF
                </button>
            </div>
            <canvas id="grafica-empleados" style="max-height: 400px;"></canvas>
        `;
        container.appendChild(chartContainer);
        canvas = document.getElementById('grafica-empleados');
    }
    
    // Destruir gráfica anterior si existe
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    // Preparar datos para la gráfica
    const empleados = reportes.map(r => r.empleado_nombre);
    const ordenes = reportes.map(r => r.cantidad_ordenes);
    const ingresos = reportes.map(r => r.ingresos_totales);
    const ganancias = reportes.map(r => r.ganancias_netas);
    
    // Crear nueva gráfica
    const ctx = canvas.getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: empleados,
            datasets: [
                {
                    label: 'Cantidad de Órdenes',
                    data: ordenes,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    yAxisID: 'y-ordenes'
                },
                {
                    label: 'Ingresos ($)',
                    data: ingresos,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 2,
                    yAxisID: 'y-dinero'
                },
                {
                    label: 'Ganancias ($)',
                    data: ganancias,
                    backgroundColor: 'rgba(255, 193, 7, 0.7)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 2,
                    yAxisID: 'y-dinero'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                title: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.dataset.yAxisID === 'y-dinero') {
                                    label += '$' + context.parsed.y.toLocaleString('es-MX', {minimumFractionDigits: 2});
                                } else {
                                    label += context.parsed.y.toLocaleString();
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                'y-ordenes': {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Cantidad de Órdenes',
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        beginAtZero: true,
                        precision: 0
                    }
                },
                'y-dinero': {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Ingresos / Ganancias ($)',
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        beginAtZero: true,
                        callback: function(value) {
                            return '$' + value.toLocaleString('es-MX');
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

async function exportarReportePDF() {
    const fechaInicio = document.getElementById('fecha-inicio-reporte').value;
    const fechaFin = document.getElementById('fecha-fin-reporte').value;
    
    if (reportesData.length === 0) {
        alert('No hay datos para exportar');
        return;
    }
    
    try {
        const response = await fetch('/admin/api/exportar-reporte-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reportes: reportesData,
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_empleados_${new Date().getTime()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            alert('✅ Reporte exportado exitosamente');
        } else {
            alert('Error al exportar el reporte');
        }
    } catch (error) {
        console.error('Error al exportar PDF:', error);
        alert('Error al exportar el reporte');
    }
}

// ===== CLIENTES =====
async function cargarClientes() {
    try {
        const response = await fetch('/admin/api/clientes');
        const data = await response.json();
        
        if (data.success) {
            mostrarClientes(data.clientes);
        }
    } catch (error) {
        console.error('Error al cargar clientes:', error);
    }
}

function mostrarClientes(clientes) {
    const tbody = document.querySelector('#tabla-clientes-admin tbody');
    tbody.innerHTML = '';
    
    if (clientes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No hay clientes registrados</td></tr>';
        return;
    }
    
    clientes.forEach(cliente => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${cliente.id}</td>
            <td>${cliente.nombre}</td>
            <td>${cliente.correo}</td>
            <td><span class="badge badge-info">${cliente.puntos_acumulados} pts</span></td>
            <td>${cliente.created_at || '-'}</td>
            <td>
                <button class="btn btn-secondary" onclick="verDetalleCliente(${cliente.id})">Ver Detalle</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ===== OTRAS FUNCIONES =====
async function cargarProductos() {
    // TODO: Implementar
    console.log('Cargar productos');
}

async function cargarCategorias() {
    // TODO: Implementar
    console.log('Cargar categorías');
}

async function cargarPerfiles() {
    // TODO: Implementar
    console.log('Cargar perfiles');
}

async function cerrarSesion() {
    if (!confirm('¿Desea cerrar sesión?')) {
        return;
    }
    
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
            alert('Error al cerrar sesión');
        }
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
        window.location.href = '/';
    }
}

// Búsqueda de clientes
document.getElementById('buscar-cliente')?.addEventListener('input', function(e) {
    const busqueda = e.target.value.toLowerCase();
    const filas = document.querySelectorAll('#tabla-clientes-admin tbody tr');
    
    filas.forEach(fila => {
        const texto = fila.textContent.toLowerCase();
        if (texto.includes(busqueda)) {
            fila.style.display = '';
        } else {
            fila.style.display = 'none';
        }
    });
});