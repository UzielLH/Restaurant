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