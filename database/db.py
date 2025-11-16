import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
import json

def get_db_connection():
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        database=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD
    )
    return conn

def validate_empleado(codigo):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT id, nombre, rol, codigo FROM empleado WHERE codigo = %s",
        (codigo,)
    )
    empleado = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return dict(empleado) if empleado else None

def get_all_productos():
    """Obtiene todos los productos con su categoría"""
    conn = get_db_connection()  # Cambiar get_connection() por get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            p.id, 
            p.categoria_id,
            c.nombre as categoria,
            p.nombre,
            p.costo,
            p.precio,
            p.precio_puntos,
            p.descripcion,
            p.img,
            p.status,
            p.created_at
        FROM producto p
        INNER JOIN categoria c ON p.categoria_id = c.id
        WHERE c.activo = true
        ORDER BY c.orden, p.nombre
    """)
    
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(prod) for prod in productos]

def get_productos_by_categoria(categoria):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT id, categoria, nombre, costo, precio, descripcion, img, status FROM producto WHERE categoria = %s ORDER BY nombre",
        (categoria,)
    )
    productos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Convertir Decimal a float
    result = []
    for p in productos:
        producto = dict(p)
        producto['costo'] = float(producto['costo'])
        producto['precio'] = float(producto['precio'])
        result.append(producto)
    
    return result if result else []

def get_categorias():
    """Obtiene todas las categorías activas (para cajero y clientes)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, nombre, descripcion, orden, activo
        FROM categoria
        WHERE activo = true
        ORDER BY orden, nombre
    """)
    
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(cat) for cat in categorias]

def get_all_categorias_admin():
    """Obtiene TODAS las categorías (activas e inactivas) para administración"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, nombre, descripcion, orden, activo, created_at
        FROM categoria
        ORDER BY orden, nombre
    """)
    
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for cat in categorias:
        categoria = dict(cat)
        categoria['created_at'] = categoria['created_at'].strftime('%Y-%m-%d %H:%M:%S') if categoria.get('created_at') else None
        result.append(categoria)
    
    return result



def guardar_venta(orden_id, cajero_id, cajero_nombre, total, pago_con, cambio, items, cliente_id=None, notas=None):
    """Guarda una venta en PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO ventas (orden_id, cajero_id, cajero_nombre, cliente_id, total, pago_con, cambio, items, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (orden_id, cajero_id, cajero_nombre, cliente_id, float(total), float(pago_con), float(cambio), json.dumps(items), notas)
        )
        venta_id = cursor.fetchone()[0]
        
        # Si hay un cliente, SOLO actualizar su última visita (NO sumar puntos aquí)
        if cliente_id:
            cursor.execute(
                """
                UPDATE cliente 
                SET ultima_visita = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (cliente_id,)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        return venta_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def get_ventas_by_cajero(cajero_id):
    """Obtiene todas las ventas de un cajero del día actual"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, orden_id, cajero_nombre, total, pago_con, cambio, 
               fecha_venta, items
        FROM ventas 
        WHERE cajero_id = %s 
        AND DATE(fecha_venta) = CURRENT_DATE
        ORDER BY fecha_venta DESC
        """,
        (cajero_id,)
    )
    ventas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for v in ventas:
        venta = dict(v)
        venta['total'] = float(venta['total'])
        venta['pago_con'] = float(venta['pago_con'])
        venta['cambio'] = float(venta['cambio'])
        venta['fecha_venta'] = venta['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(venta)
    
    return result

def get_ventas_by_cajero_turno(cajero_id, fecha_inicio):
    """Obtiene las ventas de un cajero desde una fecha específica (inicio de turno)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, orden_id, cajero_nombre, total, pago_con, cambio, 
               fecha_venta, items
        FROM ventas 
        WHERE cajero_id = %s 
        AND fecha_venta >= %s
        ORDER BY fecha_venta DESC
        """,
        (cajero_id, fecha_inicio)
    )
    ventas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for v in ventas:
        venta = dict(v)
        venta['total'] = float(venta['total'])
        venta['pago_con'] = float(venta['pago_con'])
        venta['cambio'] = float(venta['cambio'])
        venta['fecha_venta'] = venta['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(venta)
    
    return result

def get_resumen_ventas_turno(cajero_id, fecha_inicio):
    """Obtiene el resumen de ventas de un cajero desde el inicio de su turno"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT 
            COUNT(*) as cantidad_ordenes,
            COALESCE(SUM(total), 0) as total_ventas
        FROM ventas 
        WHERE cajero_id = %s 
        AND fecha_venta >= %s
        """,
        (cajero_id, fecha_inicio)
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if result:
        return {
            'cantidad_ordenes': int(result['cantidad_ordenes']),
            'total_ventas': float(result['total_ventas'])
        }
    return {'cantidad_ordenes': 0, 'total_ventas': 0.0}

def get_total_ventas_dia():
    """Obtiene el total de ventas del día actual"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT COALESCE(SUM(total), 0) as total
        FROM ventas 
        WHERE DATE(fecha_venta) = CURRENT_DATE
        """
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return float(result[0]) if result else 0.0

def get_ventas_recientes(limit=50):
    """Obtiene las ventas más recientes"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, orden_id, cajero_nombre, total, pago_con, cambio, 
               fecha_venta, items
        FROM ventas 
        ORDER BY fecha_venta DESC
        LIMIT %s
        """,
        (limit,)
    )
    ventas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for v in ventas:
        venta = dict(v)
        venta['total'] = float(venta['total'])
        venta['pago_con'] = float(venta['pago_con'])
        venta['cambio'] = float(venta['cambio'])
        venta['fecha_venta'] = venta['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(venta)
    
    return result

def get_ventas_del_dia():
    """Obtiene las ventas del día actual"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, orden_id, cajero_nombre, total, pago_con, cambio, 
               fecha_venta, items
        FROM ventas 
        WHERE DATE(fecha_venta) = CURRENT_DATE
        ORDER BY fecha_venta DESC
        """
    )
    ventas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for v in ventas:
        venta = dict(v)
        venta['total'] = float(venta['total'])
        venta['pago_con'] = float(venta['pago_con'])
        venta['cambio'] = float(venta['cambio'])
        venta['fecha_venta'] = venta['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(venta)
    
    return result

def get_venta_by_id(venta_id):
    """Obtiene una venta específica por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, orden_id, cajero_nombre, total, pago_con, cambio, 
               fecha_venta, items
        FROM ventas 
        WHERE id = %s
        """,
        (venta_id,)
    )
    venta = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if venta:
        result = dict(venta)
        result['total'] = float(result['total'])
        result['pago_con'] = float(result['pago_con'])
        result['cambio'] = float(result['cambio'])
        result['fecha_venta'] = result['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        return result
    
    return None

def guardar_cierre_caja(cajero_id, cajero_nombre, monto_inicial, total_ventas, cantidad_ordenes, monto_final, fecha_inicio):
    """Guarda un cierre de caja en PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO cierre_caja (cajero_id, cajero_nombre, monto_inicial, total_ventas, 
                                    cantidad_ordenes, monto_final, fecha_inicio)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (cajero_id, cajero_nombre, float(monto_inicial), float(total_ventas), 
             cantidad_ordenes, float(monto_final), fecha_inicio)
        )
        cierre_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return cierre_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def get_ventas_por_cajero_hoy(cajero_id):
    """Obtiene el resumen de ventas del cajero en el día actual"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT 
            COUNT(*) as cantidad_ordenes,
            COALESCE(SUM(total), 0) as total_ventas
        FROM ventas 
        WHERE cajero_id = %s 
        AND DATE(fecha_venta) = CURRENT_DATE
        """,
        (cajero_id,)
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if result:
        return {
            'cantidad_ordenes': int(result['cantidad_ordenes']),
            'total_ventas': float(result['total_ventas'])
        }
    return {'cantidad_ordenes': 0, 'total_ventas': 0.0}

def get_cierres_caja_by_cajero(cajero_id, limit=10):
    """Obtiene los últimos cierres de caja de un cajero"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, cajero_nombre, monto_inicial, total_ventas, cantidad_ordenes,
               monto_final, fecha_inicio, fecha_cierre
        FROM cierre_caja
        WHERE cajero_id = %s
        ORDER BY fecha_cierre DESC
        LIMIT %s
        """,
        (cajero_id, limit)
    )
    cierres = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for c in cierres:
        cierre = dict(c)
        cierre['monto_inicial'] = float(cierre['monto_inicial'])
        cierre['total_ventas'] = float(cierre['total_ventas'])
        cierre['monto_final'] = float(cierre['monto_final'])
        cierre['fecha_inicio'] = cierre['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S')
        cierre['fecha_cierre'] = cierre['fecha_cierre'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(cierre)
    
    return result

# Funciones para gestión de clientes
def buscar_cliente_por_correo(correo):
    """Busca un cliente por su correo electrónico"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT id, nombre, correo, puntos_acumulados, ultima_visita FROM cliente WHERE correo = %s",
        (correo,)
    )
    cliente = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if cliente:
        result = dict(cliente)
        result['ultima_visita'] = result['ultima_visita'].strftime('%Y-%m-%d %H:%M:%S') if result['ultima_visita'] else None
        return result
    return None

def crear_cliente(nombre, correo):
    """Crea un nuevo cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO cliente (nombre, correo, puntos_acumulados)
            VALUES (%s, %s, 0)
            RETURNING id
            """,
            (nombre, correo)
        )
        cliente_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return cliente_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def get_all_clientes():
    """Obtiene todos los clientes"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT id, nombre, correo, puntos_acumulados, ultima_visita, created_at FROM cliente ORDER BY nombre"
    )
    clientes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for c in clientes:
        cliente = dict(c)
        cliente['ultima_visita'] = cliente['ultima_visita'].strftime('%Y-%m-%d %H:%M:%S') if cliente['ultima_visita'] else None
        cliente['created_at'] = cliente['created_at'].strftime('%Y-%m-%d %H:%M:%S') if cliente['created_at'] else None
        result.append(cliente)
    
    return result


def get_cliente_by_id(cliente_id):
    """Obtiene un cliente por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            "SELECT id, nombre, correo, puntos_acumulados, ultima_visita, created_at FROM cliente WHERE id = %s",
            (cliente_id,)
        )
        cliente = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if cliente:
            result = dict(cliente)
            result['ultima_visita'] = result['ultima_visita'].strftime('%Y-%m-%d %H:%M:%S') if result['ultima_visita'] else None
            result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S') if result['created_at'] else None
            return result
        return None
    except Exception as e:
        print(f"Error en get_cliente_by_id: {e}")
        cursor.close()
        conn.close()
        return None

    
def descontar_puntos_cliente(cliente_id, puntos):
    """Descuenta puntos de un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE cliente 
            SET puntos_acumulados = puntos_acumulados - %s,
                ultima_visita = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING puntos_acumulados
            """,
            (puntos, cliente_id)
        )
        puntos_restantes = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return puntos_restantes
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def agregar_puntos_cliente(cliente_id, puntos):
    """Agrega puntos a un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE cliente 
            SET puntos_acumulados = puntos_acumulados + %s,
                ultima_visita = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING puntos_acumulados
            """,
            (puntos, cliente_id)
        )
        puntos_nuevos = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return puntos_nuevos
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e
    
def get_all_empleados():
    """Obtiene todos los empleados del sistema"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            id, 
            nombre, 
            rol, 
            codigo,
            created_at
        FROM empleado
        ORDER BY nombre
    """)
    
    empleados = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for emp in empleados:
        empleado = dict(emp)
        empleado['created_at'] = empleado['created_at'].strftime('%Y-%m-%d %H:%M:%S') if empleado.get('created_at') else None
        result.append(empleado)
    
    return result

def get_reportes_financieros_empleados(fecha_inicio, fecha_fin):
    """Obtiene reportes financieros agrupados por empleado"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                e.id as empleado_id,
                e.nombre as empleado_nombre,
                e.rol as empleado_rol,
                COUNT(v.id) as cantidad_ordenes,
                COALESCE(SUM(v.total), 0) as ingresos_totales,
                COALESCE(SUM(
                    (SELECT SUM((item->>'costo')::numeric * (item->>'cantidad')::integer)
                     FROM jsonb_array_elements(v.items) as item)
                ), 0) as costos_totales,
                COALESCE(SUM(v.total) - SUM(
                    (SELECT SUM((item->>'costo')::numeric * (item->>'cantidad')::integer)
                     FROM jsonb_array_elements(v.items) as item)
                ), 0) as ganancias_netas
            FROM empleado e
            LEFT JOIN ventas v ON e.id = v.cajero_id 
                AND v.fecha_venta BETWEEN %s::timestamp AND (%s || ' 23:59:59')::timestamp
            WHERE e.rol IN ('cajero', 'gerente', 'administrador')
            GROUP BY e.id, e.nombre, e.rol
            ORDER BY ingresos_totales DESC
        """, (fecha_inicio, fecha_fin))
        
        reportes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for reporte in reportes:
            result.append({
                'empleado_id': reporte['empleado_id'],
                'empleado_nombre': reporte['empleado_nombre'],
                'empleado_rol': reporte['empleado_rol'],
                'cantidad_ordenes': int(reporte['cantidad_ordenes']),
                'ingresos_totales': float(reporte['ingresos_totales']),
                'costos_totales': float(reporte['costos_totales']),
                'ganancias_netas': float(reporte['ganancias_netas'])
            })
        
        return result
        
    except Exception as e:
        print(f"Error en get_reportes_financieros_empleados: {e}")
        cursor.close()
        conn.close()
        raise e

def get_ventas_por_empleado(empleado_id, fecha_inicio, fecha_fin):
    """Obtiene todas las ventas de un empleado en un rango de fechas"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            id, 
            orden_id, 
            cajero_nombre, 
            total, 
            pago_con, 
            cambio,
            fecha_venta,
            items
        FROM ventas 
        WHERE cajero_id = %s 
        AND fecha_venta BETWEEN %s::timestamp AND (%s || ' 23:59:59')::timestamp
        ORDER BY fecha_venta DESC
    """, (empleado_id, fecha_inicio, fecha_fin))
    
    ventas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for v in ventas:
        venta = dict(v)
        venta['total'] = float(venta['total'])
        venta['pago_con'] = float(venta['pago_con'])
        venta['cambio'] = float(venta['cambio'])
        venta['fecha_venta'] = venta['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(venta)
    
    return result

# ===== FUNCIONES PARA DESCUENTOS =====
def crear_descuento_cliente(cliente_id, porcentaje_descuento, fecha_fin=None, notas=None):
    """Crea un descuento para un cliente (cliente_id puede ser NULL para descuentos generales)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Si hay cliente_id, desactivar descuentos anteriores de ese cliente
        if cliente_id:
            cursor.execute(
                "UPDATE descuento_cliente SET activo = false WHERE cliente_id = %s AND activo = true",
                (cliente_id,)
            )
        
        # Crear nuevo descuento
        cursor.execute(
            """
            INSERT INTO descuento_cliente (cliente_id, porcentaje_descuento, fecha_fin, notas)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (cliente_id, porcentaje_descuento, fecha_fin, notas)
        )
        descuento_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return descuento_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def get_all_descuentos():
    """Obtiene todos los descuentos con información del cliente (si existe)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            d.id,
            d.cliente_id,
            COALESCE(c.nombre, 'Sin cliente asignado') as cliente_nombre,
            COALESCE(c.correo, '-') as cliente_correo,
            d.porcentaje_descuento,
            d.activo,
            d.fecha_inicio,
            d.fecha_fin,
            d.notas,
            d.created_at
        FROM descuento_cliente d
        LEFT JOIN cliente c ON d.cliente_id = c.id
        ORDER BY d.created_at DESC
    """)
    
    descuentos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for desc in descuentos:
        descuento = dict(desc)
        descuento['porcentaje_descuento'] = float(descuento['porcentaje_descuento'])
        descuento['fecha_inicio'] = descuento['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S') if descuento['fecha_inicio'] else None
        descuento['fecha_fin'] = descuento['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S') if descuento['fecha_fin'] else None
        descuento['created_at'] = descuento['created_at'].strftime('%Y-%m-%d %H:%M:%S') if descuento['created_at'] else None
        result.append(descuento)
    
    return result

def get_descuento_activo_cliente(cliente_id):
    """Obtiene el descuento activo de un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            id,
            cliente_id,
            porcentaje_descuento,
            fecha_fin
        FROM descuento_cliente
        WHERE cliente_id = %s 
        AND activo = true
        AND (fecha_fin IS NULL OR fecha_fin >= CURRENT_TIMESTAMP)
        LIMIT 1
    """, (cliente_id,))
    
    descuento = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if descuento:
        result = dict(descuento)
        result['porcentaje_descuento'] = float(result['porcentaje_descuento'])
        return result
    return None

def eliminar_descuento(descuento_id):
    """Elimina un descuento (lo marca como inactivo)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE descuento_cliente SET activo = false WHERE id = %s",
            (descuento_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def eliminar_descuento_permanente(descuento_id):
    """Elimina un descuento permanentemente de la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM descuento_cliente WHERE id = %s",
            (descuento_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def get_ordenes_por_cliente(cliente_id):
    """Obtiene todas las órdenes de un cliente específico"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                id,
                orden_id,
                cajero_nombre,
                total,
                pago_con,
                cambio,
                items,
                fecha_venta,
                notas
            FROM ventas
            WHERE cliente_id = %s
            ORDER BY fecha_venta DESC
        """, (cliente_id,))
        
        ordenes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for orden in ordenes:
            orden_dict = dict(orden)
            orden_dict['total'] = float(orden_dict['total'])
            orden_dict['pago_con'] = float(orden_dict['pago_con'])
            orden_dict['cambio'] = float(orden_dict['cambio'])
            orden_dict['fecha_venta'] = orden_dict['fecha_venta'].strftime('%Y-%m-%d %H:%M:%S')
            # items ya es JSONB, se convierte automáticamente
            result.append(orden_dict)
        
        return result
        
    except Exception as e:
        print(f"Error en get_ordenes_por_cliente: {e}")
        cursor.close()
        conn.close()
        raise e
    
# ===== FUNCIONES PARA CONFIGURACIÓN DEL TICKET =====
def get_configuracion_ticket():
    """Obtiene la configuración actual del ticket"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            id,
            nombre_negocio,
            direccion,
            telefono,
            rfc,
            mensaje_agradecimiento,
            mostrar_puntos,
            encabezado,
            pie_pagina,
            logo_url,
            updated_at
        FROM configuracion_ticket
        ORDER BY id DESC
        LIMIT 1
    """)
    
    config = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if config:
        result = dict(config)
        result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if result['updated_at'] else None
        return result
    return None

def actualizar_configuracion_ticket(empleado_id, config_data):
    """Actualiza la configuración del ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Primero verificar si existe configuración
        cursor.execute("SELECT id FROM configuracion_ticket LIMIT 1")
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar configuración existente
            cursor.execute("""
                UPDATE configuracion_ticket 
                SET nombre_negocio = %s,
                    direccion = %s,
                    telefono = %s,
                    rfc = %s,
                    mensaje_agradecimiento = %s,
                    mostrar_puntos = %s,
                    encabezado = %s,
                    pie_pagina = %s,
                    logo_url = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = %s
                WHERE id = %s
                RETURNING id
            """, (
                config_data.get('nombre_negocio'),
                config_data.get('direccion'),
                config_data.get('telefono'),
                config_data.get('rfc'),
                config_data.get('mensaje_agradecimiento'),
                config_data.get('mostrar_puntos', True),
                config_data.get('encabezado'),
                config_data.get('pie_pagina'),
                config_data.get('logo_url'),
                empleado_id,
                existe[0]
            ))
        else:
            # Insertar nueva configuración
            cursor.execute("""
                INSERT INTO configuracion_ticket (
                    nombre_negocio, direccion, telefono, rfc, 
                    mensaje_agradecimiento, mostrar_puntos,
                    encabezado, pie_pagina, logo_url, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                config_data.get('nombre_negocio'),
                config_data.get('direccion'),
                config_data.get('telefono'),
                config_data.get('rfc'),
                config_data.get('mensaje_agradecimiento'),
                config_data.get('mostrar_puntos', True),
                config_data.get('encabezado'),
                config_data.get('pie_pagina'),
                config_data.get('logo_url'),
                empleado_id
            ))
        
        config_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return config_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def crear_categoria_db(nombre, descripcion, orden):
    """Crea una nueva categoría"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO categoria (nombre, descripcion, orden)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (nombre, descripcion, orden)
        )
        categoria_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return categoria_id
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def actualizar_categoria_db(categoria_id, nombre, descripcion, orden):
    """Actualiza una categoría existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE categoria 
            SET nombre = %s, descripcion = %s, orden = %s
            WHERE id = %s
            """,
            (nombre, descripcion, orden, categoria_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def eliminar_categoria_db(categoria_id):
    """Elimina una categoría (la marca como inactiva)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Marcar como inactiva en lugar de eliminar
        cursor.execute(
            "UPDATE categoria SET activo = false WHERE id = %s",
            (categoria_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

def activar_categoria_db(categoria_id):
    """Activa una categoría inactiva"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE categoria SET activo = true WHERE id = %s",
            (categoria_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e
