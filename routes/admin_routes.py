from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.redis_client import get_session
from database.db import (
    get_reportes_financieros,
    get_descuentos,
    crear_descuento,
    actualizar_descuento,
    eliminar_descuento,
    get_configuracion_ticket,
    guardar_configuracion_ticket,
    crear_categoria,
    actualizar_categoria,
    eliminar_categoria,
    crear_producto,
    actualizar_producto,
    eliminar_producto,
    crear_empleado,
    actualizar_empleado,
    eliminar_empleado,
    get_all_empleados
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def dashboard():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'administrador':
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html', empleado=empleado)

# ===== REPORTES FINANCIEROS =====
@admin_bp.route('/api/reportes-financieros', methods=['GET'])
def obtener_reportes_financieros():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'administrador':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    try:
        reportes = get_reportes_financieros(fecha_inicio, fecha_fin)
        return jsonify({'success': True, 'reportes': reportes})
    except Exception as e:
        print(f"Error al obtener reportes: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener reportes'}), 500

# ===== DESCUENTOS =====
@admin_bp.route('/api/descuentos', methods=['GET'])
def listar_descuentos():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        descuentos = get_descuentos()
        return jsonify({'success': True, 'descuentos': descuentos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/descuentos', methods=['POST'])
def crear_descuento_route():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    # TODO: Validar datos
    
    try:
        descuento_id = crear_descuento(data)
        return jsonify({'success': True, 'descuento_id': descuento_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/descuentos/<int:descuento_id>', methods=['PUT'])
def actualizar_descuento_route(descuento_id):
    # TODO: Implementar
    pass

@admin_bp.route('/api/descuentos/<int:descuento_id>', methods=['DELETE'])
def eliminar_descuento_route(descuento_id):
    # TODO: Implementar
    pass

# ===== CONFIGURACIÓN TICKET =====
@admin_bp.route('/api/configuracion-ticket', methods=['GET'])
def obtener_configuracion_ticket():
    # TODO: Implementar
    pass

@admin_bp.route('/api/configuracion-ticket', methods=['POST'])
def guardar_configuracion_ticket_route():
    # TODO: Implementar
    pass

# ===== CATEGORÍAS =====
@admin_bp.route('/api/categorias', methods=['POST'])
def crear_categoria_route():
    # TODO: Implementar
    pass

@admin_bp.route('/api/categorias/<int:categoria_id>', methods=['PUT'])
def actualizar_categoria_route(categoria_id):
    # TODO: Implementar
    pass

@admin_bp.route('/api/categorias/<int:categoria_id>', methods=['DELETE'])
def eliminar_categoria_route(categoria_id):
    # TODO: Implementar
    pass

# ===== PRODUCTOS =====
@admin_bp.route('/api/productos', methods=['POST'])
def crear_producto_route():
    # TODO: Implementar
    pass

@admin_bp.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto_route(producto_id):
    # TODO: Implementar
    pass

@admin_bp.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto_route(producto_id):
    # TODO: Implementar
    pass

# ===== PERFILES/EMPLEADOS =====
@admin_bp.route('/api/perfiles', methods=['GET'])
def listar_perfiles():
    # TODO: Implementar
    pass

@admin_bp.route('/api/perfiles', methods=['POST'])
def crear_perfil_route():
    # TODO: Implementar
    pass

@admin_bp.route('/api/perfiles/<int:perfil_id>', methods=['PUT'])
def actualizar_perfil_route(perfil_id):
    # TODO: Implementar
    pass

@admin_bp.route('/api/perfiles/<int:perfil_id>', methods=['DELETE'])
def eliminar_perfil_route(perfil_id):
    # TODO: Implementar
    pass
