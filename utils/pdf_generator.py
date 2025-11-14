from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import io

def generar_recibo_pdf(venta_data):
    """
    Genera un PDF de recibo de venta
    
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
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Contenedor para los elementos del PDF
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Estilo para info
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5
    )
    
    # Encabezado
    titulo = Paragraph("RESTAURANT LA SALLE", titulo_style)
    elementos.append(titulo)
    
    subtitulo = Paragraph("Recibo de Compra", subtitulo_style)
    elementos.append(subtitulo)
    
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información de la venta
    fecha_format = datetime.strptime(venta_data['fecha_venta'], '%Y-%m-%d %H:%M:%S')
    fecha_str = fecha_format.strftime('%d/%m/%Y %I:%M %p')
    
    info_data = [
        ['Orden:', venta_data['orden_id'][:8].upper()],
        ['Fecha:', fecha_str],
        ['Cajero:', venta_data['cajero_nombre']],
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#667eea')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elementos.append(info_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Línea separadora
    line_data = [['_' * 80]]
    line_table = Table(line_data, colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elementos.append(line_table)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Tabla de productos
    productos_data = [['Cant.', 'Producto', 'P. Unit.', 'Subtotal']]
    
    for item in venta_data['items']:
        cantidad = int(item['cantidad'])
        nombre = item['nombre']
        precio = float(item['precio'])
        subtotal = precio * cantidad
        
        productos_data.append([
            str(cantidad),
            nombre,
            f"${precio:.2f}",
            f"${subtotal:.2f}"
        ])
    
    productos_table = Table(productos_data, colWidths=[0.8*inch, 3*inch, 1.2*inch, 1.2*inch])
    productos_table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Contenido
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Líneas
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#667eea')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elementos.append(productos_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Totales
    total = float(venta_data['total'])
    pago_con = float(venta_data['pago_con'])
    cambio = float(venta_data['cambio'])
    
    totales_data = [
        ['Subtotal:', f"${total:.2f}"],
        ['Total:', f"${total:.2f}"],
        ['Pagó con:', f"${pago_con:.2f}"],
    ]
    
    if cambio > 0:
        totales_data.append(['Cambio:', f"${cambio:.2f}"])
    
    totales_table = Table(totales_data, colWidths=[4.5*inch, 1.5*inch])
    totales_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -2), 'Helvetica', 11),
        ('FONT', (0, -1), (0, -1), 'Helvetica-Bold', 12),
        ('FONT', (1, 0), (1, -2), 'Helvetica', 11),
        ('FONT', (1, -1), (1, -1), 'Helvetica-Bold', 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#667eea')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#667eea')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elementos.append(totales_table)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Mensaje de agradecimiento
    gracias_style = ParagraphStyle(
        'Gracias',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#667eea'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    mensaje_gracias = Paragraph("¡Gracias por su compra!", gracias_style)
    elementos.append(mensaje_gracias)
    
    mensaje_final = Paragraph("Esperamos verle pronto", subtitulo_style)
    elementos.append(mensaje_final)
    
    # Construir PDF
    doc.build(elementos)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
