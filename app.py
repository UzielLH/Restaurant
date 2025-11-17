from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import uuid
from config import Config
from database.db import validate_empleado, get_all_productos, get_categorias, guardar_venta, get_venta_by_id, guardar_cierre_caja, get_ventas_por_cajero_hoy, get_cierres_caja_by_cajero, get_ventas_by_cajero, buscar_cliente_por_correo, crear_cliente, get_all_clientes, get_ventas_by_cajero_turno, get_resumen_ventas_turno
from database.db import get_descuento_activo_cliente, eliminar_descuento_permanente
from database.redis_client import save_session, get_session, save_caja_inicial, save_orden, get_all_ordenes, get_orden, delete_orden, update_orden_status, actualizar_caja, get_caja_actual, get_ordenes_pendientes, get_caja_inicial_original, set_caja_inicial_original, get_fecha_inicio_sesion, set_fecha_inicio_sesion, limpiar_sesion_completa
from datetime import datetime
from utils.pdf_generator import generar_recibo_pdf
from routes.admin_routes import admin_bp
from routes.gerente_routes import gerente_bp
import io

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(admin_bp)
app.register_blueprint(gerente_bp)
@app.route('/')
def index():
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    codigo = data.get('codigo')
    
    if not codigo or len(codigo) != 4:
        return jsonify({'success': False, 'message': 'Código inválido'}), 400
    
    empleado = validate_empleado(codigo)
    
    if not empleado:
        return jsonify({'success': False, 'message': 'Código incorrecto'}), 401
    
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    save_session(session_id, empleado)
    
    return jsonify({
        'success': True,
        'empleado': empleado,
        'requires_caja': empleado['rol'] == 'cajero'
    })

@app.route('/api/set-caja', methods=['POST'])
def set_caja():
    data = request.get_json()
    monto = data.get('monto')
    session_id = session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': 'Sesión no válida'}), 401
    
    try:
        monto = float(monto)
        if monto < 0:
            return jsonify({'success': False, 'message': 'Monto inválido'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Monto inválido'}), 400
    
    # Guardar monto inicial
    save_caja_inicial(session_id, monto)
    # Guardar monto inicial original (sin modificar)
    set_caja_inicial_original(session_id, monto)
    # Guardar fecha de inicio
    set_fecha_inicio_sesion(session_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    return jsonify({'success': True, 'message': 'Caja inicial guardada'})

@app.route('/dashboard')
def dashboard():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    empleado = get_session(session_id)
    if not empleado:
        return redirect(url_for('index'))
    
    # Redirigir según el rol
    if empleado['rol'] == 'administrador':
        return redirect(url_for('admin.dashboard'))
    elif empleado['rol'] == 'cajero':
        return redirect(url_for('cajero'))
    elif empleado['rol'] == 'gerente':
        return redirect(url_for('gerente_dashboard'))
    elif empleado['rol'] == 'cocinero':
        return redirect(url_for('cocinero_dashboard'))  # Nueva ruta para cocinero
    
    return render_template('dashboard.html', empleado=empleado)

@app.route('/cocinero')
def cocinero_dashboard():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'cocinero':
        return redirect(url_for('index'))
    
    return render_template('cocinero_dashboard.html', empleado=empleado)

@app.route('/gerente')
def gerente_dashboard():
    return redirect(url_for('gerente.dashboard'))


# @app.route('/admin')
# def admin_dashboard():
#     session_id = session.get('session_id')
#     if not session_id:
#         return redirect(url_for('index'))
    
#     empleado = get_session(session_id)
#     if not empleado or empleado['rol'] != 'administrador':
#         return redirect(url_for('index'))
    
#     return render_template('admin_dashboard.html', empleado=empleado)


@app.route('/cajero')
def cajero():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    empleado = get_session(session_id)
    if not empleado or empleado['rol'] != 'cajero':
        return redirect(url_for('index'))
    
    categorias = get_categorias()
    productos = get_all_productos()
    
    return render_template('cajero.html', empleado=empleado, categorias=categorias, productos=productos)

@app.route('/api/productos', methods=['GET'])
def get_productos():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    productos = get_all_productos()
    return jsonify({'success': True, 'productos': productos})

@app.route('/api/crear-orden', methods=['POST'])
def crear_orden():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    data = request.get_json()
    items = data.get('items', [])
    notas = data.get('notas')
    cliente_id = data.get('cliente_id')
    
    if not items:
        return jsonify({'success': False, 'message': 'La orden está vacía'}), 400
    
    # Convertir precios a float para asegurar cálculo correcto
    for item in items:
        item['precio'] = float(item['precio'])
        item['costo'] = float(item.get('costo', 0))
        item['cantidad'] = int(item['cantidad'])
    
    # Calcular total
    total = sum(float(item['precio']) * int(item['cantidad']) for item in items)
    
    # Obtener nombre del cliente si existe
    cliente_nombre = None
    if cliente_id:
        from database.db import get_cliente_by_id
        cliente = get_cliente_by_id(cliente_id)
        if cliente:
            cliente_nombre = cliente['nombre']
    
    # Crear orden
    orden_id = str(uuid.uuid4())
    orden = {
        'orden_id': orden_id,
        'items': items,
        'total': float(total),
        'status': 'pendiente',
        'cajero': empleado['nombre'],
        'cajero_id': empleado['id'],
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'notas': notas,
        'cliente_id': cliente_id,
        'cliente_nombre': cliente_nombre
    }
    
    print(f"Guardando orden: {orden}")  # Debug
    save_orden(orden_id, orden)
    
    return jsonify({
        'success': True,
        'message': 'Orden creada',
        'orden_id': orden_id,
        'orden': orden
    })

@app.route('/api/ordenes', methods=['GET'])
def listar_ordenes():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    # Obtener solo órdenes pendientes
    ordenes = get_ordenes_pendientes()
    return jsonify({'success': True, 'ordenes': ordenes})

@app.route('/api/orden/<orden_id>', methods=['GET'])
def obtener_orden(orden_id):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    orden = get_orden(orden_id)
    if not orden:
        return jsonify({'success': False, 'message': 'Orden no encontrada'}), 404
    
    return jsonify({'success': True, 'orden': orden})

@app.route('/api/procesar-pago', methods=['POST'])
def procesar_pago():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    data = request.get_json()
    orden_id = data.get('orden_id')
    pago_con = data.get('pago_con')
    cliente_id = data.get('cliente_id')
    descuento_id = data.get('descuento_id')
    descuento_porcentaje = data.get('descuento_porcentaje')
    total_original = data.get('total_original')
    
    # Validar datos
    try:
        pago_con = float(pago_con)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Monto de pago inválido'}), 400
    
    # Obtener orden
    orden = get_orden(orden_id)
    if not orden:
        return jsonify({'success': False, 'message': 'Orden no encontrada'}), 404
    
    if orden.get('status') == 'pagada':
        return jsonify({'success': False, 'message': 'Esta orden ya fue pagada'}), 400
    
    # Usar cliente_id de la orden si existe y no viene del frontend
    if not cliente_id and orden.get('cliente_id'):
        cliente_id = orden.get('cliente_id')
    
    # Si hay descuento, verificar que todavía existe y está activo
    descuento_aplicado = False
    descuento_monto = 0
    total_final = float(orden['total'])
    notas_descuento = None
    
    if descuento_id and cliente_id:
        try:
            # Verificar que el descuento sigue activo
            descuento = get_descuento_activo_cliente(cliente_id)
            
            if descuento and descuento['id'] == descuento_id:
                # Calcular descuento
                total_sin_descuento = float(total_original) if total_original else total_final
                descuento_monto = (total_sin_descuento * float(descuento_porcentaje)) / 100
                total_final = total_sin_descuento - descuento_monto
                descuento_aplicado = True
                
                # Preparar notas del descuento
                notas_descuento = f"Descuento aplicado: {descuento_porcentaje}% (-${descuento_monto:.2f}). Total original: ${total_sin_descuento:.2f}. Total con descuento: ${total_final:.2f}"
                
                if descuento.get('notas'):
                    notas_descuento += f"\nMotivo del descuento: {descuento['notas']}"
        except Exception as e:
            print(f"Error al verificar descuento: {e}")
            # Continuar sin descuento si hay error
    
    # Validar que el pago sea suficiente
    if pago_con < total_final:
        return jsonify({
            'success': False, 
            'message': f'El pago es insuficiente. Falta: ${(total_final - pago_con):.2f}'
        }), 400
    
    # Calcular cambio
    cambio = pago_con - total_final
    
    # Verificar que hay suficiente efectivo para dar cambio
    if cambio > 0:
        caja_actual = get_caja_actual(session_id)
        if caja_actual is not None:
            caja_despues_cambio = caja_actual + total_final - cambio
            if caja_despues_cambio < 0:
                return jsonify({
                    'success': False,
                    'message': f'No hay suficiente efectivo en caja para dar cambio.\nCambio requerido: ${cambio:.2f}\nEfectivo disponible: ${caja_actual:.2f}\nPor favor solicite un monto más cercano al total.'
                }), 400
    
    try:
        # Combinar notas de la orden con notas del descuento
        notas_finales = orden.get('notas', '')
        if notas_descuento:
            if notas_finales:
                notas_finales = f"{notas_finales}\n\n{notas_descuento}"
            else:
                notas_finales = notas_descuento
        
        # Guardar venta en PostgreSQL
        venta_id = guardar_venta(
            orden_id=orden_id,
            cajero_id=empleado['id'],
            cajero_nombre=empleado['nombre'],
            total=total_final,
            pago_con=pago_con,
            cambio=cambio,
            items=orden['items'],
            cliente_id=cliente_id,
            notas=notas_finales
        )
        
        # Calcular puntos ganados (5% del total) - SOLO para pago con efectivo
        puntos_ganados = 0
        puntos_nuevos = None
        if cliente_id:
            from database.db import agregar_puntos_cliente
            puntos_ganados = int(total_final * 0.05)  # 5% en puntos del total con descuento
            puntos_nuevos = agregar_puntos_cliente(cliente_id, puntos_ganados)
        
        # Si hubo descuento, eliminarlo de la base de datos
        if descuento_aplicado and descuento_id:
            try:
                eliminar_descuento_permanente(descuento_id)
                print(f"Descuento {descuento_id} eliminado exitosamente")
            except Exception as e:
                print(f"Error al eliminar descuento: {e}")
                # No fallar la transacción si hay error al eliminar el descuento
        
        # Actualizar monto en caja (sumar el total de la venta)
        caja_actualizada = actualizar_caja(session_id, total_final)
        
        # Actualizar estado de orden en Redis
        update_orden_status(orden_id, 'pagada')
        
        response_data = {
            'success': True,
            'message': 'Pago procesado exitosamente',
            'venta_id': venta_id,
            'cambio': cambio,
            'caja_actual': caja_actualizada,
            'puntos_ganados': puntos_ganados if cliente_id else None,
            'puntos_nuevos': puntos_nuevos
        }
        
        # Agregar información del descuento si fue aplicado
        if descuento_aplicado:
            response_data['descuento_aplicado'] = True
            response_data['descuento_porcentaje'] = descuento_porcentaje
            response_data['descuento_monto'] = descuento_monto
            response_data['total_original'] = total_original if total_original else total_final + descuento_monto
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error al procesar pago: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al procesar el pago'
        }), 500

@app.route('/api/generar-recibo/<int:venta_id>', methods=['GET'])
def generar_recibo(venta_id):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        # Obtener datos de la venta
        venta = get_venta_by_id(venta_id)
        
        if not venta:
            return jsonify({'success': False, 'message': 'Venta no encontrada'}), 404
        
        # Generar PDF
        pdf = generar_recibo_pdf(venta)
        
        # Crear nombre de archivo
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"recibo_{venta_id}_{fecha}.pdf"
        
        # Enviar PDF como respuesta
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error al generar recibo: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al generar el recibo'
        }), 500

@app.route('/api/caja-actual', methods=['GET'])
def obtener_caja_actual():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    caja_actual = get_caja_actual(session_id)
    
    if caja_actual is None:
        return jsonify({'success': False, 'message': 'No se encontró información de caja'}), 404
    
    return jsonify({
        'success': True,
        'caja_actual': caja_actual
    })

@app.route('/api/resumen-caja', methods=['GET'])
def resumen_caja():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    try:
        # Obtener información de la caja
        monto_inicial = get_caja_inicial_original(session_id)
        caja_actual = get_caja_actual(session_id)
        fecha_inicio = get_fecha_inicio_sesion(session_id)
        
        if monto_inicial is None or caja_actual is None or fecha_inicio is None:
            return jsonify({'success': False, 'message': 'No se encontró información de caja'}), 404
        
        # Obtener resumen de ventas SOLO del turno actual (desde fecha_inicio)
        ventas_resumen = get_resumen_ventas_turno(empleado['id'], fecha_inicio)
        
        # Obtener lista de ventas SOLO del turno actual
        ventas_turno = get_ventas_by_cajero_turno(empleado['id'], fecha_inicio)
        
        return jsonify({
            'success': True,
            'resumen': {
                'cajero': empleado['nombre'],
                'cajero_id': empleado['id'],
                'monto_inicial': float(monto_inicial),
                'monto_actual': float(caja_actual),
                'total_ventas': float(ventas_resumen['total_ventas']),
                'cantidad_ordenes': int(ventas_resumen['cantidad_ordenes']),
                'fecha_inicio': fecha_inicio,
                'ventas': ventas_turno
            }
        })
        
    except Exception as e:
        print(f"Error al obtener resumen de caja: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al obtener resumen de caja: {str(e)}'
        }), 500

@app.route('/api/cerrar-caja', methods=['POST'])
def cerrar_caja():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    try:
        # Obtener información de la caja
        monto_inicial = get_caja_inicial_original(session_id)
        monto_final = get_caja_actual(session_id)
        fecha_inicio = get_fecha_inicio_sesion(session_id)
        
        if monto_inicial is None or monto_final is None or fecha_inicio is None:
            return jsonify({'success': False, 'message': 'No se encontró información de caja'}), 404
        
        # Obtener resumen de ventas SOLO del turno actual
        ventas_resumen = get_resumen_ventas_turno(empleado['id'], fecha_inicio)
        
        # Guardar cierre de caja
        cierre_id = guardar_cierre_caja(
            cajero_id=empleado['id'],
            cajero_nombre=empleado['nombre'],
            monto_inicial=monto_inicial,
            total_ventas=ventas_resumen['total_ventas'],
            cantidad_ordenes=ventas_resumen['cantidad_ordenes'],
            monto_final=monto_final,
            fecha_inicio=fecha_inicio
        )
        
        return jsonify({
            'success': True,
            'message': 'Cierre de caja guardado exitosamente',
            'cierre_id': cierre_id
        })
        
    except Exception as e:
        print(f"Error al cerrar caja: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al cerrar caja'
        }), 500

@app.route('/api/cerrar-sesion', methods=['POST'])
def cerrar_sesion():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        # Limpiar completamente la sesión en Redis
        limpiar_sesion_completa(session_id)
        
        # Clear session in Flask
        session.clear()
        
        return jsonify({'success': True, 'message': 'Sesión cerrada correctamente'})
    except Exception as e:
        print(f"Error al cerrar sesión: {e}")
        return jsonify({'success': False, 'message': 'Error al cerrar sesión'}), 500

@app.route('/api/buscar-cliente', methods=['GET'])
def buscar_cliente():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    correo = request.args.get('correo')
    if not correo:
        return jsonify({'success': False, 'message': 'Correo requerido'}), 400
    
    cliente = buscar_cliente_por_correo(correo)
    
    if cliente:
        return jsonify({'success': True, 'cliente': cliente})
    else:
        return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404

@app.route('/api/crear-cliente', methods=['POST'])
def crear_cliente_route():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    nombre = data.get('nombre')
    correo = data.get('correo')
    
    if not nombre or not correo:
        return jsonify({'success': False, 'message': 'Nombre y correo son requeridos'}), 400
    
    try:
        cliente_id = crear_cliente(nombre, correo)
        return jsonify({
            'success': True,
            'message': 'Cliente creado exitosamente',
            'cliente_id': cliente_id
        })
    except Exception as e:
        print(f"Error al crear cliente: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al crear cliente. El correo podría estar duplicado.'
        }), 500

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    clientes = get_all_clientes()
    return jsonify({'success': True, 'clientes': clientes})



@app.route('/api/cliente/<int:cliente_id>', methods=['GET'])
def obtener_cliente(cliente_id):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        from database.db import get_cliente_by_id
        cliente = get_cliente_by_id(cliente_id)
        
        if cliente:
            return jsonify({'success': True, 'cliente': cliente})
        else:
            return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404
    except Exception as e:
        print(f"Error al obtener cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener cliente'}), 500



@app.route('/api/procesar-pago-puntos', methods=['POST'])
def procesar_pago_puntos():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    data = request.get_json()
    orden_id = data.get('orden_id')
    cliente_id = data.get('cliente_id')
    puntos_necesarios = data.get('puntos_necesarios')
    
    if not cliente_id:
        return jsonify({'success': False, 'message': 'Cliente requerido para pago con puntos'}), 400
    
    if not puntos_necesarios or puntos_necesarios <= 0:
        return jsonify({'success': False, 'message': 'Puntos necesarios inválidos'}), 400
    
    # Obtener orden
    orden = get_orden(orden_id)
    if not orden:
        return jsonify({'success': False, 'message': 'Orden no encontrada'}), 404
    
    if orden.get('status') == 'pagada':
        return jsonify({'success': False, 'message': 'Esta orden ya fue pagada'}), 400
    
    total = float(orden['total'])
    
    try:
        # Obtener cliente y verificar puntos
        from database.db import get_cliente_by_id, descontar_puntos_cliente
        
        cliente = get_cliente_by_id(cliente_id)
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404
        
        puntos_disponibles = cliente['puntos_acumulados']
        
        if puntos_disponibles < puntos_necesarios:
            return jsonify({
                'success': False, 
                'message': f'Puntos insuficientes. Tiene {puntos_disponibles}, necesita {puntos_necesarios}'
            }), 400
        
        # Descontar puntos ANTES de guardar la venta
        puntos_restantes = descontar_puntos_cliente(cliente_id, puntos_necesarios)
        
        # Preparar desglose de productos para las notas
        desglose_puntos = []
        for item in orden['items']:
            precio_puntos = int(item.get('precio_puntos', 0))
            cantidad = int(item.get('cantidad', 1))
            subtotal_puntos = precio_puntos * cantidad
            desglose_puntos.append(f"{item['nombre']} (x{cantidad}): {subtotal_puntos} pts")
        
        notas_pago = f"Pago con puntos.\nPuntos usados: {puntos_necesarios}\nDesglose:\n" + "\n".join(desglose_puntos)
        
        # Guardar venta con método de pago "puntos"
        venta_id = guardar_venta(
            orden_id=orden_id,
            cajero_id=empleado['id'],
            cajero_nombre=empleado['nombre'],
            total=total,
            pago_con=0,  # Pago con puntos
            cambio=0,
            items=orden['items'],
            cliente_id=cliente_id,
            notas=notas_pago
        )
        
        # Actualizar estado de orden en Redis
        update_orden_status(orden_id, 'pagada')
        
        # No actualizar caja porque fue pago con puntos (no ingresó dinero físico)
        
        return jsonify({
            'success': True,
            'message': 'Pago con puntos procesado exitosamente',
            'venta_id': venta_id,
            'puntos_usados': puntos_necesarios,
            'puntos_restantes': puntos_restantes
        })
        
    except Exception as e:
        print(f"Error al procesar pago con puntos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al procesar el pago con puntos'
        }), 500

@app.route('/api/cancelar-orden/<orden_id>', methods=['DELETE'])
def cancelar_orden(orden_id):
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    empleado = get_session(session_id)
    if not empleado:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401
    
    try:
        # Verificar que la orden existe
        orden = get_orden(orden_id)
        if not orden:
            return jsonify({'success': False, 'message': 'Orden no encontrada'}), 404
        
        # Verificar que la orden no esté pagada
        if orden.get('status') == 'pagada':
            return jsonify({'success': False, 'message': 'No se puede cancelar una orden ya pagada'}), 400
        
        # Eliminar la orden de Redis
        delete_orden(orden_id)
        
        return jsonify({
            'success': True,
            'message': 'Orden cancelada exitosamente'
        })
        
    except Exception as e:
        print(f"Error al cancelar orden: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al cancelar la orden'
        }), 500

# Agregar esta nueva ruta después de las rutas existentes
@app.route('/api/descuento-cliente/<int:cliente_id>', methods=['GET'])
def obtener_descuento_cliente(cliente_id):
    """Obtiene el descuento activo de un cliente"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        descuento = get_descuento_activo_cliente(cliente_id)
        
        if descuento:
            return jsonify({
                'success': True,
                'descuento': descuento
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No hay descuento activo para este cliente'
            })
    except Exception as e:
        print(f"Error al obtener descuento: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener descuento'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)