from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db import (
    get_all_productos,
    get_producto_by_id,
    actualizar_producto_db,
    cambiar_status_producto_db,
    get_all_categorias_admin
)
from database.redis_client import get_session

gerente_bp = Blueprint('gerente', __name__, url_prefix='/gerente')

@gerente_bp.route('/dashboard')
def dashboard():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return redirect(url_for('index'))
    
    return render_template('gerente_dashboard.html', empleado=empleado)

# ===== API ENDPOINTS PARA PRODUCTOS =====

@gerente_bp.route('/api/productos-gerente', methods=['GET'])
def get_productos_gerente():
    """Obtiene todos los productos para el gerente"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        productos = get_all_productos()
        return jsonify({
            'success': True,
            'productos': productos
        })
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener productos'
        }), 500

@gerente_bp.route('/api/productos/<int:producto_id>', methods=['GET'])
def get_producto(producto_id):
    """Obtiene un producto específico"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        producto = get_producto_by_id(producto_id)
        
        if producto:
            return jsonify({
                'success': True,
                'producto': producto
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
    except Exception as e:
        print(f"Error al obtener producto: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener producto'
        }), 500

@gerente_bp.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    """Actualiza un producto existente"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('nombre') or not data.get('categoria_id') or not data.get('costo') or not data.get('precio'):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos'
            }), 400
        
        # Actualizar producto
        actualizar_producto_db(producto_id, data)
        
        return jsonify({
            'success': True,
            'message': 'Producto actualizado exitosamente'
        })
        
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al actualizar producto'
        }), 500

@gerente_bp.route('/api/productos/<int:producto_id>/desactivar', methods=['PUT'])
def desactivar_producto(producto_id):
    """Desactiva un producto"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        cambiar_status_producto_db(producto_id, 'fuera de servicio')
        
        return jsonify({
            'success': True,
            'message': 'Producto desactivado exitosamente'
        })
        
    except Exception as e:
        print(f"Error al desactivar producto: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al desactivar producto'
        }), 500

@gerente_bp.route('/api/productos/<int:producto_id>/activar', methods=['PUT'])
def activar_producto(producto_id):
    """Activa un producto"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        cambiar_status_producto_db(producto_id, 'disponible')
        
        return jsonify({
            'success': True,
            'message': 'Producto activado exitosamente'
        })
        
    except Exception as e:
        print(f"Error al activar producto: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al activar producto'
        }), 500

@gerente_bp.route('/api/categorias-gerente', methods=['GET'])
def get_categorias_gerente():
    """Obtiene todas las categorías activas para el gerente"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        categorias = get_all_categorias_admin()
        
        return jsonify({
            'success': True,
            'categorias': categorias
        })
        
    except Exception as e:
        print(f"Error al obtener categorías: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener categorías'
        }), 500

# ===== DESCUENTOS =====
@gerente_bp.route('/api/descuentos', methods=['GET'])
def listar_descuentos():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from database.db import get_all_descuentos
        descuentos = get_all_descuentos()
        return jsonify({'success': True, 'descuentos': descuentos})
    except Exception as e:
        print(f"Error al obtener descuentos: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener descuentos'}), 500

@gerente_bp.route('/api/descuentos', methods=['POST'])
def crear_descuento():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    data = request.get_json()
    cliente_id = data.get('cliente_id') or None
    porcentaje_descuento = data.get('porcentaje_descuento')
    fecha_fin = data.get('fecha_fin') or None
    notas = data.get('notas') or None
    
    if not porcentaje_descuento:
        return jsonify({'success': False, 'message': 'El porcentaje de descuento es requerido'}), 400
    
    try:
        from database.db import crear_descuento_cliente
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

@gerente_bp.route('/api/descuentos/<int:descuento_id>', methods=['DELETE'])
def eliminar_descuento_route(descuento_id):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from database.db import eliminar_descuento_permanente
        eliminar_descuento_permanente(descuento_id)
        return jsonify({'success': True, 'message': 'Descuento eliminado exitosamente'})
    except Exception as e:
        print(f"Error al eliminar descuento: {e}")
        return jsonify({'success': False, 'message': 'Error al eliminar descuento'}), 500

@gerente_bp.route('/api/clientes', methods=['GET'])
def listar_clientes():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'gerente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from database.db import get_all_clientes
        clientes = get_all_clientes()
        return jsonify({'success': True, 'clientes': clientes})
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener clientes'}), 500