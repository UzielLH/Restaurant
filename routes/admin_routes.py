from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
from database.redis_client import get_session
from database.db import (
    get_all_empleados,
    get_ventas_por_empleado,
    get_reportes_financieros_empleados,
    get_all_clientes,
    get_all_productos,
    get_categorias,
    get_all_categorias_admin, 
    crear_descuento_cliente,
    get_all_descuentos,
    eliminar_descuento_permanente
)
from utils.pdf_reports import generar_reporte_empleados_pdf
import io
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')  # Cambiar de '/dashboard' a '/'
def dashboard():
    empleado = verificar_admin()
    if not empleado:
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html', empleado=empleado)

def verificar_admin():
    """Middleware para verificar que el usuario es administrador"""
    session_id = session.get('session_id')
    if not session_id:
        return None
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'administrador':
        return None
    
    return empleado

# ===== REPORTES FINANCIEROS =====
@admin_bp.route('/api/reportes-empleados', methods=['GET'])
def obtener_reportes_empleados():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    # Si no se proporcionan fechas, usar últimos 30 días
    if not fecha_inicio or not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        reportes = get_reportes_financieros_empleados(fecha_inicio, fecha_fin)
        return jsonify({'success': True, 'reportes': reportes})
    except Exception as e:
        print(f"Error al obtener reportes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener reportes'}), 500

@admin_bp.route('/api/exportar-reporte-pdf', methods=['POST'])
def exportar_reporte_pdf():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    reportes = data.get('reportes', [])
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    
    try:
        pdf = generar_reporte_empleados_pdf(reportes, fecha_inicio, fecha_fin)
        
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reporte_empleados_{fecha}.pdf"
        
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al generar PDF'}), 500

# ===== CLIENTES =====
@admin_bp.route('/api/clientes', methods=['GET'])
def listar_clientes():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        clientes = get_all_clientes()
        return jsonify({'success': True, 'clientes': clientes})
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener clientes'}), 500

# ===== PRODUCTOS =====
@admin_bp.route('/api/productos-admin', methods=['GET'])
def listar_productos():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import get_all_productos
        productos = get_all_productos()
        return jsonify({'success': True, 'productos': productos})
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener productos'}), 500

# ===== CATEGORÍAS =====
@admin_bp.route('/api/categorias-admin', methods=['GET'])
def listar_categorias():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        categorias = get_all_categorias_admin()  # ← Cambiar a usar la nueva función
        return jsonify({'success': True, 'categorias': categorias})
    except Exception as e:
        print(f"Error al obtener categorías: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener categorías'}), 500

# ===== EMPLEADOS/PERFILES =====
@admin_bp.route('/api/empleados', methods=['GET'])
def listar_empleados():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        empleados = get_all_empleados()
        return jsonify({'success': True, 'empleados': empleados})
    except Exception as e:
        print(f"Error al obtener empleados: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener empleados'}), 500
    
# ===== DESCUENTOS =====
@admin_bp.route('/api/descuentos', methods=['GET'])
def listar_descuentos():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        descuentos = get_all_descuentos()
        return jsonify({'success': True, 'descuentos': descuentos})
    except Exception as e:
        print(f"Error al obtener descuentos: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener descuentos'}), 500

@admin_bp.route('/api/descuentos', methods=['POST'])
def crear_descuento():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    cliente_id = data.get('cliente_id') or None  # Convertir cadena vacía a None
    porcentaje_descuento = data.get('porcentaje_descuento')
    fecha_fin = data.get('fecha_fin') or None
    notas = data.get('notas') or None
    
    # Validar solo el porcentaje (cliente_id es opcional)
    if not porcentaje_descuento:
        return jsonify({'success': False, 'message': 'El porcentaje de descuento es requerido'}), 400
    
    try:
        porcentaje = float(porcentaje_descuento)
        if porcentaje < 0 or porcentaje > 100:
            return jsonify({'success': False, 'message': 'El porcentaje debe estar entre 0 y 100'}), 400
        
        descuento_id = crear_descuento_cliente(cliente_id, porcentaje, fecha_fin, notas)
        return jsonify({'success': True, 'message': 'Descuento creado exitosamente', 'descuento_id': descuento_id})
    except Exception as e:
        print(f"Error al crear descuento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error al crear descuento: {str(e)}'}), 500

@admin_bp.route('/api/descuentos/<int:descuento_id>', methods=['DELETE'])
def eliminar_descuento_route(descuento_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        eliminar_descuento_permanente(descuento_id)
        return jsonify({'success': True, 'message': 'Descuento eliminado exitosamente'})
    except Exception as e:
        print(f"Error al eliminar descuento: {e}")
        return jsonify({'success': False, 'message': 'Error al eliminar descuento'}), 500
    

@admin_bp.route('/api/clientes/<int:cliente_id>/detalle', methods=['GET'])
def obtener_detalle_cliente(cliente_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import get_cliente_by_id, get_ordenes_por_cliente
        
        cliente = get_cliente_by_id(cliente_id)
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404
        
        ordenes = get_ordenes_por_cliente(cliente_id)
        
        return jsonify({
            'success': True,
            'cliente': cliente,
            'ordenes': ordenes
        })
    except Exception as e:
        print(f"Error al obtener detalle del cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener detalle'}), 500

# ===== CONFIGURACIÓN DEL TICKET =====
@admin_bp.route('/api/configuracion-ticket', methods=['GET'])
def obtener_configuracion_ticket():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import get_configuracion_ticket
        config = get_configuracion_ticket()
        return jsonify({'success': True, 'configuracion': config})
    except Exception as e:
        print(f"Error al obtener configuración: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener configuración'}), 500

@admin_bp.route('/api/configuracion-ticket', methods=['POST'])
def actualizar_configuracion_ticket_route():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import actualizar_configuracion_ticket
        data = request.get_json()
        
        config_id = actualizar_configuracion_ticket(empleado['id'], data)
        return jsonify({'success': True, 'message': 'Configuración actualizada exitosamente', 'config_id': config_id})
    except Exception as e:
        print(f"Error al actualizar configuración: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error al actualizar configuración: {str(e)}'}), 500
    
    
# ===== CATEGORÍAS =====
@admin_bp.route('/api/categorias', methods=['POST'])
def crear_categoria():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    orden = data.get('orden', 0)
    
    if not nombre:
        return jsonify({'success': False, 'message': 'El nombre es requerido'}), 400
    
    try:
        from database.db import crear_categoria_db
        categoria_id = crear_categoria_db(nombre, descripcion, orden)
        return jsonify({'success': True, 'message': 'Categoría creada exitosamente', 'categoria_id': categoria_id})
    except Exception as e:
        print(f"Error al crear categoría: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/categorias/<int:categoria_id>', methods=['PUT'])
def actualizar_categoria(categoria_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    orden = data.get('orden', 0)
    
    if not nombre:
        return jsonify({'success': False, 'message': 'El nombre es requerido'}), 400
    
    try:
        from database.db import actualizar_categoria_db
        actualizar_categoria_db(categoria_id, nombre, descripcion, orden)
        return jsonify({'success': True, 'message': 'Categoría actualizada exitosamente'})
    except Exception as e:
        print(f"Error al actualizar categoría: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/categorias/<int:categoria_id>', methods=['DELETE'])
def eliminar_categoria_route(categoria_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import eliminar_categoria_db
        eliminar_categoria_db(categoria_id)
        return jsonify({'success': True, 'message': 'Categoría eliminada exitosamente'})
    except Exception as e:
        print(f"Error al eliminar categoría: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/categorias/<int:categoria_id>/activar', methods=['PUT'])
def activar_categoria(categoria_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import activar_categoria_db
        activar_categoria_db(categoria_id)
        return jsonify({'success': True, 'message': 'Categoría activada exitosamente'})
    except Exception as e:
        print(f"Error al activar categoría: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
# ===== PRODUCTOS =====
@admin_bp.route('/api/productos', methods=['POST'])
def crear_producto():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    
    try:
        from database.db import crear_producto_db
        producto_id = crear_producto_db(data)
        return jsonify({'success': True, 'message': 'Producto creado exitosamente', 'producto_id': producto_id})
    except Exception as e:
        print(f"Error al crear producto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/productos/<int:producto_id>', methods=['GET'])
def obtener_producto(producto_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import get_producto_by_id
        producto = get_producto_by_id(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
        return jsonify({'success': True, 'producto': producto})
    except Exception as e:
        print(f"Error al obtener producto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    
    try:
        from database.db import actualizar_producto_db
        actualizar_producto_db(producto_id, data)
        return jsonify({'success': True, 'message': 'Producto actualizado exitosamente'})
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/productos/<int:producto_id>/desactivar', methods=['PUT'])
def desactivar_producto(producto_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import cambiar_status_producto_db
        cambiar_status_producto_db(producto_id, 'fuera de servicio')
        return jsonify({'success': True, 'message': 'Producto desactivado exitosamente'})
    except Exception as e:
        print(f"Error al desactivar producto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/productos/<int:producto_id>/activar', methods=['PUT'])
def activar_producto(producto_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import cambiar_status_producto_db
        cambiar_status_producto_db(producto_id, 'disponible')
        return jsonify({'success': True, 'message': 'Producto activado exitosamente'})
    except Exception as e:
        print(f"Error al activar producto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== EMPLEADOS/PERFILES =====
@admin_bp.route('/api/empleados', methods=['POST'])
def crear_empleado():
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    
    try:
        from database.db import crear_empleado_db
        empleado_id = crear_empleado_db(data)
        return jsonify({'success': True, 'message': 'Perfil creado exitosamente', 'empleado_id': empleado_id})
    except Exception as e:
        print(f"Error al crear empleado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/empleados/<int:empleado_id>', methods=['PUT'])
def actualizar_empleado(empleado_id):
    empleado = verificar_admin()
    if not empleado:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    
    try:
        from database.db import actualizar_empleado_db
        actualizar_empleado_db(empleado_id, data)
        return jsonify({'success': True, 'message': 'Perfil actualizado exitosamente'})
    except Exception as e:
        print(f"Error al actualizar empleado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

