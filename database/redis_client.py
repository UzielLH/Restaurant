import redis
import json
from config import Config

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)

def save_session(session_id, data):
    redis_client.setex(
        f"session:{session_id}",
        Config.SESSION_TIMEOUT,
        json.dumps(data)
    )

def get_session(session_id):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

def delete_session(session_id):
    redis_client.delete(f"session:{session_id}")

def save_caja_inicial(session_id, monto):
    key = f"caja:{session_id}"
    redis_client.setex(key, Config.SESSION_TIMEOUT, monto)

def get_caja_inicial(session_id):
    return redis_client.get(f"caja:{session_id}")

def get_caja_inicial_original(session_id):
    """Obtiene el monto inicial de caja (sin modificaciones)"""
    monto = redis_client.get(f"caja_inicial:{session_id}")
    return float(monto) if monto else None

def set_caja_inicial_original(session_id, monto):
    """Guarda el monto inicial de caja en una key separada"""
    redis_client.setex(
        f"caja_inicial:{session_id}",
        Config.SESSION_TIMEOUT,
        str(float(monto))
    )

def actualizar_caja(session_id, monto_agregar):
    """Actualiza el monto de la caja sumando la ganancia"""
    caja_actual = get_caja_inicial(session_id)
    if caja_actual:
        nuevo_monto = float(caja_actual) + float(monto_agregar)
        key = f"caja:{session_id}"
        redis_client.setex(key, Config.SESSION_TIMEOUT, nuevo_monto)
        return nuevo_monto
    return None

def get_caja_actual(session_id):
    """Obtiene el monto actual de la caja"""
    monto = redis_client.get(f"caja:{session_id}")
    return float(monto) if monto else None

def save_orden(orden_id, data):
    """Guarda una orden en Redis"""
    redis_client.setex(
        f"orden:{orden_id}",
        Config.SESSION_TIMEOUT,
        json.dumps(data)
    )

def get_orden(orden_id):
    """Obtiene una orden específica"""
    data = redis_client.get(f"orden:{orden_id}")
    return json.loads(data) if data else None

def get_all_ordenes():
    """Obtiene todas las órdenes activas"""
    keys = redis_client.keys("orden:*")
    ordenes = []
    for key in keys:
        data = redis_client.get(key)
        if data:
            try:
                orden = json.loads(data)
                # Asegurar que orden_id esté presente
                if 'orden_id' not in orden:
                    orden['orden_id'] = key.split('orden:')[-1] if ':' in key else key.replace('orden:', '')
                ordenes.append(orden)
            except json.JSONDecodeError:
                print(f"Error al decodificar orden: {key}")
                continue
    return ordenes

def delete_orden(orden_id):
    """Elimina una orden de Redis"""
    redis_client.delete(f"orden:{orden_id}")

def update_orden_status(orden_id, status):
    """Actualiza el estado de una orden"""
    orden = get_orden(orden_id)
    if orden:
        if status == 'pagada':
            # Si la orden está pagada, la eliminamos de Redis
            # porque ya está guardada en PostgreSQL
            delete_orden(orden_id)
            return True
        else:
            orden['status'] = status
            save_orden(orden_id, orden)
            return True
    return False

def get_ordenes_pendientes():
    """Obtiene solo las órdenes pendientes (no pagadas)"""
    keys = redis_client.keys("orden:*")
    ordenes = []
    for key in keys:
        data = redis_client.get(key)
        if data:
            try:
                orden = json.loads(data)
                # Solo incluir órdenes pendientes
                if orden.get('status') == 'pendiente':
                    if 'orden_id' not in orden:
                        orden['orden_id'] = key.split('orden:')[-1] if ':' in key else key.replace('orden:', '')
                    ordenes.append(orden)
            except json.JSONDecodeError:
                print(f"Error al decodificar orden: {key}")
                continue
    return ordenes

def get_fecha_inicio_sesion(session_id):
    """Obtiene la fecha de inicio de sesión"""
    fecha = redis_client.get(f"fecha_inicio:{session_id}")
    return fecha if fecha else None

def set_fecha_inicio_sesion(session_id, fecha):
    """Guarda la fecha de inicio de sesión"""
    redis_client.setex(
        f"fecha_inicio:{session_id}",
        Config.SESSION_TIMEOUT,
        str(fecha)
    )

def limpiar_sesion_completa(session_id):
    """Elimina todos los datos de Redis relacionados con una sesión"""
    # Eliminar sesión del empleado
    redis_client.delete(f"session:{session_id}")
    
    # Eliminar información de caja
    redis_client.delete(f"caja:{session_id}")
    redis_client.delete(f"caja_inicial:{session_id}")
    
    # Eliminar fecha de inicio
    redis_client.delete(f"fecha_inicio:{session_id}")
    
    # Eliminar todas las órdenes pendientes (opcional, ya que son generales no por sesión)
    # Si quieres eliminar solo las órdenes del cajero específico, necesitarías
    # agregar el session_id o cajero_id a la key de las órdenes
    
    return True
