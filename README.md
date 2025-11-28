# Restaurant Management System - README

## 📋 Descripción del Proyecto

Sistema integral de gestión para restaurantes que incluye módulos para administración, gerencia, cajeros y cocina. Desarrollado con Flask, PostgreSQL, Redis y Socket.IO para comunicación en tiempo real.

## 🚀 Características Principales

- **Módulo de Administración**: Gestión completa de reportes financieros, productos, categorías, empleados, clientes y descuentos
- **Módulo de Gerencia**: Gestión de platillos, descuentos y acceso al punto de venta
- **Módulo de Cajero**: Punto de venta completo con gestión de órdenes, pagos en efectivo/puntos y cierre de caja
- **Módulo de Cocina**: Vista en tiempo real de órdenes pendientes con notificaciones mediante WebSockets
- **Sistema de Clientes**: Registro de clientes, acumulación de puntos (5% del total de compra) y descuentos personalizados
- **Generación de Tickets PDF**: Recibos de venta personalizables con logo del negocio

## 📦 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** - [Descargar aquí](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Descargar aquí](https://www.postgresql.org/download/)
- **Redis 6+** - [Descargar aquí](https://redis.io/download/)
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)

## 🛠️ Instalación y Configuración

### 1. Clonar o Descargar el Proyecto

```bash
# Si usas Git
git clone <url-del-repositorio>
cd Restaurant

# O descargar el ZIP y extraer en la carpeta deseada
```

### 2. Crear Entorno Virtual de Python

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

Si no existe `requirements.txt`, instalar manualmente:

```bash
pip install flask flask-socketio psycopg2-binary redis reportlab python-dotenv
```

### 4. Configurar PostgreSQL

#### 4.1 Crear Base de Datos

Abrir **pgAdmin** o **psql** y ejecutar:

```sql
CREATE DATABASE restaurant_db;
```

#### 4.2 Ejecutar Script de Inicialización

Ejecutar el script SQL ubicado en `database/init_db.sql`:

**Opción 1 - Desde pgAdmin:**
1. Conectar a la base de datos `restaurant_db`
2. Ir a **Tools** > **Query Tool**
3. Abrir el archivo `database/init_db.sql`
4. Ejecutar el script (F5)

**Opción 2 - Desde línea de comandos:**

```bash
# Windows (PowerShell o CMD)
psql -U postgres -d restaurant_db -f database\init_db.sql

# Linux/Mac
psql -U postgres -d restaurant_db -f database/init_db.sql
```

**Nota:** Reemplazar `postgres` con tu usuario de PostgreSQL si es diferente.

#### 4.3 Verificar Tablas Creadas

```sql
-- Conectarse a restaurant_db y ejecutar:
\dt  -- En psql

-- O en pgAdmin, verificar las siguientes tablas:
-- categoria, empleado, cliente, producto, ventas, 
-- cierre_caja, descuento_cliente, configuracion_ticket
```

### 5. Configurar Redis

#### 5.1 Instalar Redis

**Windows:**
- Descargar desde [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- Instalar y ejecutar `redis-server.exe`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Mac:**
```bash
brew install redis
brew services start redis
```

#### 5.2 Verificar Redis

```bash
redis-cli ping
# Debe responder: PONG
```

### 6. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# filepath: .env
SECRET_KEY=tu-clave-secreta-super-segura-aqui

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=tu-password-postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**⚠️ IMPORTANTE:** Reemplazar `tu-password-postgres` con tu contraseña real de PostgreSQL.

### 7. Verificar Estructura del Proyecto

Asegurarse de que la estructura sea similar a:

```
Restaurant/
├── app.py                      # Aplicación principal
├── config.py                   # Configuración
├── requirements.txt            # Dependencias
├── .env                        # Variables de entorno (crear)
├── database/
│   ├── db.py                   # Conexión a PostgreSQL
│   ├── redis_client.py         # Cliente Redis
│   └── init_db.sql             # Script de inicialización ✅
├── routes/
│   ├── admin_routes.py         # Rutas de administrador
│   └── gerente_routes.py       # Rutas de gerente
├── utils/
│   └── pdf_generator.py        # Generador de PDFs
├── static/                     # Archivos estáticos (CSS, JS)
└── templates/                  # Plantillas HTML
```

## 🚀 Ejecutar la Aplicación

### 1. Activar Entorno Virtual (si no está activo)

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Verificar Servicios

Asegurarse de que estén corriendo:
- **PostgreSQL** (puerto 5432)
- **Redis** (puerto 6379)

### 3. Iniciar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 👥 Usuarios de Prueba

El script `init_db.sql` crea los siguientes empleados de prueba:

| Nombre | Rol | Código |
|--------|-----|--------|
| Juan Pérez | Gerente | `1234` |
| María García | Cajero | `5678` |
| Carlos López | Administrador | `9012` |
| Pedro Ramírez | Cocinero | `3456` |

También crea 3 clientes de prueba:
- Ana Martínez (ana.martinez@email.com) - 150 puntos
- Roberto Silva (roberto.silva@email.com) - 300 puntos
- Laura Gómez (laura.gomez@email.com) - 75 puntos

## 📚 Estructura de la Base de Datos

### Tablas Principales

1. **categoria**: Categorías de productos (Bebidas, Entradas, Plato Fuerte, Postres)
2. **empleado**: Usuarios del sistema (gerente, cajero, administrador, cocinero)
3. **cliente**: Clientes con sistema de puntos
4. **producto**: Productos del menú con precios en efectivo y puntos
5. **ventas**: Registro de todas las ventas realizadas
6. **cierre_caja**: Historial de cierres de caja por cajero
7. **descuento_cliente**: Descuentos personalizados para clientes
8. **configuracion_ticket**: Configuración personalizable de tickets PDF

### Relaciones Importantes

- `producto.categoria_id` → `categoria.id`
- `ventas.cajero_id` → `empleado.id`
- `ventas.cliente_id` → `cliente.id`
- `descuento_cliente.cliente_id` → `cliente.id`

## 🔧 Funcionalidades por Módulo

### Administrador (Código: 9012)
- Dashboard con reportes financieros y gráficas
- CRUD completo de productos y categorías
- Gestión de empleados
- Gestión de clientes y descuentos
- Consulta de historial de ventas y cierres de caja
- Configuración de tickets personalizados

### Gerente (Código: 1234)
- Acceso al dashboard de administración
- Gestión de productos y categorías
- Creación de descuentos para clientes
- Acceso al punto de venta (módulo cajero)

### Cajero (Código: 5678)
- Apertura de caja (monto inicial)
- Crear órdenes con productos del menú
- Procesar pagos en efectivo o con puntos
- Buscar/crear clientes
- Aplicar descuentos activos
- Generar tickets PDF
- Consultar resumen de caja
- Cerrar caja al finalizar turno

### Cocinero (Código: 3456)
- Vista en tiempo real de órdenes pendientes
- Notificaciones instantáneas de nuevas órdenes (WebSockets)
- Marcar órdenes como vistas
- Interfaz limpia enfocada en preparación de alimentos

## 🔐 Seguridad

- Autenticación por código de 4 dígitos
- Sesiones manejadas con Redis
- Validación de roles para acceso a funcionalidades
- Restricciones de FK en base de datos
- Variables sensibles en `.env` (no incluir en Git)

## 🐛 Solución de Problemas

### PostgreSQL no se conecta
```bash
# Verificar que el servicio esté corriendo
# Windows: Services → PostgreSQL
# Linux: sudo systemctl status postgresql
```

### Redis no se conecta
```bash
# Verificar servicio
redis-cli ping
# Debe responder: PONG

# Reiniciar Redis si es necesario
# Windows: Reiniciar redis-server.exe
# Linux: sudo systemctl restart redis-server
```

### Error "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
```

### Error en init_db.sql
- Verificar que la base de datos `restaurant_db` exista
- Revisar sintaxis del SQL (hay una coma faltante en línea 90)
- Ejecutar línea por línea si hay errores

## 📝 Notas Adicionales

- **Sistema de Puntos**: Los clientes ganan 5% del total de compra en puntos
- **Descuentos**: Se pueden crear descuentos permanentes o temporales para clientes
- **Tickets PDF**: Personalizables con logo, información fiscal y legal
- **WebSockets**: Comunicación en tiempo real entre cajeros y cocineros
- **Cierre de Caja**: Registra todas las transacciones del turno del cajero

## 🤝 Contribuciones

Para contribuir al proyecto:
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es para uso educativo - La Salle, Séptimo Semestre, Servidores Web.

## 📧 Contacto

Para dudas o soporte, contactar al equipo de desarrollo.

---

**Última actualización:** Noviembre 2025