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
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT id, categoria, nombre, costo, precio, precio_puntos, descripcion, img, status FROM producto ORDER BY categoria, nombre"
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
        producto['precio_puntos'] = int(producto.get('precio_puntos', 0))
        result.append(producto)
    
    return result if result else []

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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT DISTINCT categoria FROM producto ORDER BY categoria"
    )
    categorias = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [c[0] for c in categorias] if categorias else []

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
        "SELECT id, nombre, correo, puntos_acumulados, ultima_visita FROM cliente ORDER BY nombre"
    )
    clientes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    result = []
    for c in clientes:
        cliente = dict(c)
        cliente['ultima_visita'] = cliente['ultima_visita'].strftime('%Y-%m-%d %H:%M:%S') if cliente['ultima_visita'] else None
        result.append(cliente)
    
    return result


def get_cliente_by_id(cliente_id):
    """Obtiene un cliente por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            "SELECT id, nombre, correo, puntos_acumulados, ultima_visita FROM cliente WHERE id = %s",
            (cliente_id,)
        )
        cliente = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if cliente:
            result = dict(cliente)
            result['ultima_visita'] = result['ultima_visita'].strftime('%Y-%m-%d %H:%M:%S') if result['ultima_visita'] else None
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