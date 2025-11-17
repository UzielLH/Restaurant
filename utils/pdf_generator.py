from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import io
import requests
from io import BytesIO

def generar_recibo_pdf(venta_data):
    """
    Genera un PDF de recibo de venta para impresora de tickets (80mm)
    
    Args:
        venta_data: dict con los datos de la venta
            - orden_id: ID de la orden
            - cajero_nombre: Nombre del cajero
            - items: Lista de productos
            - total: Total de la venta
            - pago_con: Monto con el que pagó
            - cambio: Cambio devuelto
            - fecha_venta: Fecha de la venta
    """
    from database.db import get_configuracion_ticket
    
    buffer = io.BytesIO()
    
    # Obtener configuración del ticket
    config = get_configuracion_ticket()
    if not config:
        config = {
            'nombre_negocio': 'RESTAURANT LA SALLE',
            'direccion': '',
            'telefono': '',
            'rfc': '',
            'encabezado': '',
            'mensaje_agradecimiento': '¡Gracias por su compra!',
            'pie_pagina': '',
            'mostrar_puntos': True,
            'logo_url': None
        }
    
    # Tamaño de ticket de 80mm de ancho (con márgenes mínimos)
    ticket_width = 80 * mm
    ticket_height = 297 * mm  # Altura variable
    
    # Crear documento PDF con tamaño de ticket
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(ticket_width, ticket_height),
        rightMargin=5*mm,
        leftMargin=5*mm,
        topMargin=5*mm,
        bottomMargin=5*mm
    )
    
    elementos = []
    styles = getSampleStyleSheet()
    
    # Ancho disponible para contenido
    ancho_contenido = ticket_width - 10*mm
    
    # ========== ESTILOS PERSONALIZADOS ==========
    titulo_style = ParagraphStyle(
        'TituloTicket',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=3
    )
    
    info_style = ParagraphStyle(
        'InfoTicket',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=2
    )
    
    header_style = ParagraphStyle(
        'HeaderTicket',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=1
    )
    
    dato_style = ParagraphStyle(
        'DatoTicket',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT,
        spaceAfter=1
    )
    
    separador_style = ParagraphStyle(
        'Separador',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    # ========== LOGO ==========
    if config.get('logo_url'):
        try:
            response = requests.get(config['logo_url'], timeout=5)
            if response.status_code == 200:
                img_buffer = BytesIO(response.content)
                logo = Image(img_buffer, width=30*mm, height=15*mm)
                logo.hAlign = 'CENTER'
                elementos.append(logo)
                elementos.append(Spacer(1, 2*mm))
        except Exception as e:
            print(f"Error al cargar logo: {e}")
    
    # ========== ENCABEZADO - NOMBRE DEL NEGOCIO ==========
    titulo = Paragraph(config.get('nombre_negocio', 'RESTAURANT LA SALLE'), titulo_style)
    elementos.append(titulo)
    
    # ========== INFORMACIÓN DEL NEGOCIO ==========
    if config.get('direccion'):
        elementos.append(Paragraph(config['direccion'], info_style))
    if config.get('telefono'):
        elementos.append(Paragraph(f"Tel: {config['telefono']}", info_style))
    if config.get('rfc'):
        elementos.append(Paragraph(f"RFC: {config['rfc']}", info_style))
    
    elementos.append(Spacer(1, 2*mm))
    
    # ========== ENCABEZADO LEGAL ==========
    if config.get('encabezado'):
        for linea in config['encabezado'].split('\n'):
            if linea.strip():
                elementos.append(Paragraph(linea.strip(), header_style))
        elementos.append(Spacer(1, 2*mm))
    
    # ========== SEPARADOR ==========
    elementos.append(Paragraph('=' * 42, separador_style))
    elementos.append(Paragraph('TICKET DE COMPRA', info_style))
    elementos.append(Paragraph('=' * 42, separador_style))
    elementos.append(Spacer(1, 2*mm))
    
    # ========== INFORMACIÓN DE LA VENTA ==========
    fecha_format = datetime.strptime(venta_data['fecha_venta'], '%Y-%m-%d %H:%M:%S')
    fecha_str = fecha_format.strftime('%d/%m/%Y %I:%M %p')
    
    dato_bold_style = ParagraphStyle(
        'DatoBold',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT,
        spaceAfter=1
    )
    
    elementos.append(Paragraph(f"Orden: {venta_data['orden_id'][:8].upper()}", dato_bold_style))
    elementos.append(Paragraph(f"Fecha: {fecha_str}", dato_style))
    elementos.append(Paragraph(f"Cajero: {venta_data['cajero_nombre']}", dato_style))
    
    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph('-' * 42, separador_style))
    
    # ========== TABLA DE PRODUCTOS ==========
    # Encabezado de productos
    productos_header = [['Cant', 'Producto', 'Importe']]
    
    for item in venta_data['items']:
        cantidad = int(item['cantidad'])
        nombre = item['nombre']
        precio = float(item['precio'])
        subtotal = precio * cantidad
        
        # Limitar nombre a 20 caracteres para que quepa
        nombre_corto = nombre[:20] if len(nombre) > 20 else nombre
        
        productos_header.append([
            str(cantidad),
            nombre_corto,
            f"${subtotal:.2f}"
        ])
    
    # Crear tabla con anchos específicos para ticket de 80mm
    tabla_productos = Table(
        productos_header, 
        colWidths=[10*mm, 40*mm, 20*mm]
    )
    
    tabla_productos.setStyle(TableStyle([
        # Encabezado
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, 0), 2),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        
        # Contenido
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
    ]))
    
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph('-' * 42, separador_style))
    
    # ========== TOTALES ==========
    total = float(venta_data['total'])
    pago_con = float(venta_data['pago_con'])
    cambio = float(venta_data['cambio'])
    
    # Estilo para totales normales
    total_normal_style = ParagraphStyle(
        'TotalNormal',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT
    )
    
    # Estilo para TOTAL en negrita
    total_bold_style = ParagraphStyle(
        'TotalBold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    totales_data = [
        [Paragraph('Subtotal:', total_normal_style), Paragraph(f"${total:.2f}", total_normal_style)],
        [Paragraph('TOTAL:', total_bold_style), Paragraph(f"${total:.2f}", total_bold_style)],
        [Paragraph('Pagó con:', total_normal_style), Paragraph(f"${pago_con:.2f}", total_normal_style)]
    ]
    
    if cambio > 0:
        totales_data.append([
            Paragraph('Su cambio:', total_normal_style), 
            Paragraph(f"${cambio:.2f}", total_normal_style)
        ])
    
    tabla_totales = Table(totales_data, colWidths=[40*mm, 30*mm])
    tabla_totales.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
    ]))
    
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 3*mm))
    
    # ========== PIE DE PÁGINA ==========
    if config.get('pie_pagina'):
        elementos.append(Paragraph('=' * 42, separador_style))
        for linea in config['pie_pagina'].split('\n'):
            if linea.strip():
                elementos.append(Paragraph(linea.strip(), header_style))
        elementos.append(Spacer(1, 2*mm))
    
    # ========== MENSAJE DE AGRADECIMIENTO ==========
    elementos.append(Paragraph('=' * 42, separador_style))
    
    mensaje_gracias_style = ParagraphStyle(
        'Gracias',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    elementos.append(Paragraph(
        config.get('mensaje_agradecimiento', '¡Gracias por su compra!'), 
        mensaje_gracias_style
    ))
    elementos.append(Paragraph('Esperamos verle pronto', info_style))
    
    elementos.append(Spacer(1, 5*mm))
    
    # Construir PDF
    doc.build(elementos)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf