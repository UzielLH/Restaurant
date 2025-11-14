CREATE TABLE IF NOT EXISTS empleado (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('gerente', 'cajero', 'administrador')),
    codigo CHAR(4) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    puntos_acumulados INTEGER DEFAULT 0,
    ultima_visita TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS producto (
    id SERIAL PRIMARY KEY,
    categoria VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    costo DECIMAL(10, 2) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    precio_puntos INTEGER DEFAULT 0,
    descripcion TEXT,
    img VARCHAR(255),
    status VARCHAR(20) NOT NULL CHECK (status IN ('disponible', 'fuera de servicio')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    orden_id VARCHAR(255) NOT NULL,
    cajero_id INTEGER NOT NULL,
    cajero_nombre VARCHAR(100) NOT NULL,
    cliente_id INTEGER,
    total DECIMAL(10, 2) NOT NULL,
    pago_con DECIMAL(10, 2) NOT NULL,
    cambio DECIMAL(10, 2) NOT NULL,
    items JSONB NOT NULL,
    notas TEXT,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cajero_id) REFERENCES empleado(id),
    FOREIGN KEY (cliente_id) REFERENCES cliente(id)
);

CREATE TABLE IF NOT EXISTS cierre_caja (
    id SERIAL PRIMARY KEY,
    cajero_id INTEGER NOT NULL,
    cajero_nombre VARCHAR(100) NOT NULL,
    monto_inicial DECIMAL(10, 2) NOT NULL,
    total_ventas DECIMAL(10, 2) NOT NULL,
    cantidad_ordenes INTEGER NOT NULL,
    monto_final DECIMAL(10, 2) NOT NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cajero_id) REFERENCES empleado(id)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);
CREATE INDEX IF NOT EXISTS idx_ventas_cajero ON ventas(cajero_id);
CREATE INDEX IF NOT EXISTS idx_ventas_orden ON ventas(orden_id);
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cierre_caja_fecha ON cierre_caja(fecha_cierre);
CREATE INDEX IF NOT EXISTS idx_cierre_caja_cajero ON cierre_caja(cajero_id);
CREATE INDEX IF NOT EXISTS idx_cliente_correo ON cliente(correo);

-- Datos de ejemplo
INSERT INTO empleado (nombre, rol, codigo) VALUES
('Juan Pérez', 'gerente', '1234'),
('María García', 'cajero', '5678'),
('Carlos López', 'administrador', '9012')
ON CONFLICT (codigo) DO NOTHING;

-- Datos de ejemplo para clientes
INSERT INTO cliente (nombre, correo, puntos_acumulados) VALUES
('Ana Martínez', 'ana.martinez@email.com', 150),
('Roberto Silva', 'roberto.silva@email.com', 300),
('Laura Gómez', 'laura.gomez@email.com', 75)
ON CONFLICT (correo) DO NOTHING;

-- Datos de ejemplo para productos con precio_puntos
INSERT INTO producto (categoria, nombre, costo, precio, precio_puntos, descripcion, img, status) VALUES
-- Bebidas
('Bebidas', 'Coca Cola', 8.00, 15.00, 50, 'Refresco 600ml', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCC0n-t7TY1uTtMap9hY0RH15PZ2WZC1YPsw&s', 'disponible'),
('Bebidas', 'Agua Natural', 5.00, 10.00, 30, 'Agua embotellada 500ml', 'https://carnemart.com/wp-content/uploads/2025/10/wp-image-4998.jpg', 'disponible'),
('Bebidas', 'Jugo de Naranja', 12.00, 25.00, 80, 'Jugo natural recién exprimido', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Orange_juice_1.jpg/960px-Orange_juice_1.jpg', 'disponible'),
('Bebidas', 'Café Americano', 8.00, 20.00, 65, 'Café recién preparado', 'https://upload.wikimedia.org/wikipedia/commons/4/45/A_small_cup_of_coffee.JPG', 'disponible'),
('Bebidas', 'Té Helado', 10.00, 22.00, 70, 'Té frío con limón', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQTMmDpprSHjbB_Iqh_zep0wG3BXEnpcuPIQ&s', 'fuera de servicio'),

-- Entradas
('Entradas', 'Ensalada César', 25.00, 65.00, 200, 'Lechuga, pollo, crutones y aderezo césar', 'https://www.goodnes.com/sites/g/files/jgfbjl321/files/srh_recipes/755f697272cbcdc6e5df2adb44b1b705.jpg', 'disponible'),
('Entradas', 'Alitas Buffalo', 30.00, 85.00, 280, '8 piezas con salsa picante', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTa8HRKDMKr9M9ZkURAZhP6tt8TmvRZJhKtoA&s', 'disponible'),
('Entradas', 'Nachos con Queso', 20.00, 55.00, 180, 'Nachos gratinados con queso cheddar', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSG7WANtVSujRjGbTm-5rSRp2ieoygK4KHxSQ&s', 'disponible'),
('Entradas', 'Dedos de Queso', 22.00, 60.00, 195, '6 piezas con salsa marinara', 'https://i.blogs.es/531290/mozzarella-sticks/840_560.jpg', 'disponible'),
('Entradas', 'Sopa del Día', 18.00, 45.00, 145, 'Consultar con mesero', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT5TJpHZlEqZcYJArGy-TkbK8khghlb-IqTWg&s', 'disponible'),

-- Plato Fuerte
('Plato Fuerte', 'Hamburguesa Clásica', 35.00, 95.00, 320, 'Carne 180g, lechuga, tomate, queso', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSddjpE64jVcMqw9x270i2vfbklSHIt-LzP7w&s', 'disponible'),
('Plato Fuerte', 'Pizza Pepperoni', 40.00, 120.00, 400, 'Pizza familiar con pepperoni', 'https://www.sortirambnens.com/wp-content/uploads/2019/02/pizza-de-peperoni.jpg', 'disponible'),
('Plato Fuerte', 'Tacos al Pastor', 30.00, 80.00, 260, '4 tacos con cebolla y cilantro', 'https://comedera.com/wp-content/uploads/sites/9/2017/08/tacos-al-pastor-receta.jpg', 'disponible'),
('Plato Fuerte', 'Filete de Res', 60.00, 180.00, 600, '250g con papas y verduras', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQmn0--E_S_ic0SIBRfvYMOuX7i5LnY5dw8Xg&s', 'disponible'),
('Plato Fuerte', 'Pasta Alfredo', 28.00, 85.00, 280, 'Fettuccine con salsa cremosa', 'https://images.aws.nestle.recipes/resized/cc72869fabfc2bdfa036fd1fe0e2bad8_creamy_alfredo_pasta_long_left_1200_628.jpg', 'disponible'),
('Plato Fuerte', 'Salmón a la Plancha', 55.00, 165.00, 550, 'Con arroz blanco y ensalada', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOaa3MY15iBwNEFkQSSpCbbcgCcxj3Erjr7Q&s', 'fuera de servicio'),
('Plato Fuerte', 'Pollo Asado', 32.00, 90.00, 300, 'Medio pollo con guarnición', 'https://sandersonfarms.com/wp-content/uploads/2017/04/Recipes_Roast_Chicken_with_Garlic_and_Lime_Thumb_420x420.jpg', 'disponible'),

-- Postres
('Postres', 'Pastel de Chocolate', 20.00, 55.00, 180, 'Rebanada de pastel con helado', 'https://assets.tmecosys.com/image/upload/t_web_rdp_recipe_584x480_1_5x/img/recipe/ras/Assets/5054EE1D-15EE-412C-8AA1-72A4DA244E34/Derivates/90ADA8E1-6472-4BC8-9846-E06D88BE4211.jpg', 'disponible'),
('Postres', 'Cheesecake', 22.00, 60.00, 195, 'Cheesecake de fresa', 'https://assets.tmecosys.com/image/upload/t_web_rdp_recipe_584x480_1_5x/img/recipe/ras/Assets/B4908103-C61E-4BCC-9609-03919F55CE7E/Derivates/60B07F46-E017-4FDD-A6A9-BDA7A09C6240.jpg', 'disponible'),
('Postres', 'Helado', 15.00, 40.00, 130, '3 bolas a elegir', 'https://happyvegannie.com/wp-content/uploads/2024/06/helado-de-fresa-vegano-1200x1200-1.jpg', 'disponible'),
('Postres', 'Flan Napolitano', 18.00, 45.00, 145, 'Flan casero con caramelo', 'https://assets.tmecosys.com/image/upload/t_web_rdp_recipe_584x480/img/recipe/ras/Assets/32121D5E-D3DF-4FD9-BE6E-7EB53562A1DE/Derivates/02DCA6F3-23D3-4F25-92B2-EAEF2A6606F3.jpg', 'disponible'),
('Postres', 'Brownie', 20.00, 50.00, 165, 'Con nuez y helado de vainilla', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSKla3fUU5QCsD_mA39sf3JCn6Hf3VANGa1nQ&s', 'fuera de servicio')
ON CONFLICT DO NOTHING;
