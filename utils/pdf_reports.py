from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

def generar_reporte_empleados_pdf(reportes, fecha_inicio, fecha_fin):
    """Genera un PDF con el reporte financiero de empleados"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Contenedor para los elementos del PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Título
    elements.append(Paragraph("REPORTE FINANCIERO POR EMPLEADO", title_style))
    
    # Fecha del reporte
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Generado el: {fecha_reporte}", subtitle_style))
    
    # Rango de fechas
    fecha_inicio_format = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
    fecha_fin_format = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
    elements.append(Paragraph(f"Período: {fecha_inicio_format} - {fecha_fin_format}", subtitle_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Resumen general
    total_ordenes = sum(r['cantidad_ordenes'] for r in reportes)
    total_ingresos = sum(r['ingresos_totales'] for r in reportes)
    total_costos = sum(r['costos_totales'] for r in reportes)
    total_ganancias = sum(r['ganancias_netas'] for r in reportes)
    
    elements.append(Paragraph("RESUMEN GENERAL", heading_style))
    
    resumen_data = [
        ['Métrica', 'Valor'],
        ['Total de Órdenes', f"{total_ordenes:,}"],
        ['Ingresos Totales', f"${total_ingresos:,.2f}"],
        ['Costos Totales', f"${total_costos:,.2f}"],
        ['Ganancias Netas', f"${total_ganancias:,.2f}"],
    ]
    
    resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(resumen_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Tabla de empleados
    elements.append(Paragraph("DETALLE POR EMPLEADO", heading_style))
    
    # Preparar datos de la tabla
    data = [['Empleado', 'Rol', 'Órdenes', 'Ingresos', 'Costos', 'Ganancias']]
    
    for reporte in reportes:
        data.append([
            reporte['empleado_nombre'],
            reporte['empleado_rol'].capitalize(),
            str(reporte['cantidad_ordenes']),
            f"${reporte['ingresos_totales']:,.2f}",
            f"${reporte['costos_totales']:,.2f}",
            f"${reporte['ganancias_netas']:,.2f}"
        ])
    
    # Crear tabla
    table = Table(data, colWidths=[1.8*inch, 1*inch, 0.8*inch, 1.3*inch, 1.3*inch, 1.3*inch])
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Cuerpo de la tabla
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Pie de página con información adicional
    elements.append(Spacer(1, 0.5*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", footer_style))
    elements.append(Paragraph("Este reporte fue generado automáticamente por el sistema de gestión", footer_style))
    elements.append(Paragraph(f"© {datetime.now().year} - Sistema de Punto de Venta", footer_style))
    
    # Construir PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf