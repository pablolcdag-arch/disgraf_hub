from fastapi import APIRouter, Request
from fastapi.responses import Response
from dependencies import get_current_user, DATA_DIR
import os
import json
import datetime
import uuid
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

EMISOR_NOMBRE = os.environ.get("EMISOR_NOMBRE", "DISGRAF Insumos Gráficos")
EMISOR_RAZON_SOCIAL = os.environ.get("EMISOR_RAZON_SOCIAL", "Pablo Stiefel")
EMISOR_CUIT = os.environ.get("EMISOR_CUIT", "20-30254446-9")
EMISOR_CONDICION_IVA = os.environ.get("EMISOR_CONDICION_IVA", "IVA Responsable Inscripto")
EMISOR_DOMICILIO = os.environ.get("EMISOR_DOMICILIO", "Dr. Juan Felipe Aranguren 49 CABA")
EMISOR_INGRESOS_BRUTOS = os.environ.get("EMISOR_INGRESOS_BRUTOS", "20302544469")

router = APIRouter()

import sqlite3

@router.post("/api/cotizador/guardar")
async def api_log_quote(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    data = await request.json()
    client_name = data.get("client_name", "Consumidor Final")
    if not client_name.strip():
        client_name = "Consumidor Final"
        
    total = data.get("total", 0)
    products = data.get("products", [])
    
    is_reprint = data.get("is_reprint", False)
    quote_id = data.get("quote_id") or data.get("id")
    if is_reprint or quote_id:
        return {"status": "success", "message": "Reimpresión ignorada en historial"}
    
    # Construir mensaje para Telegram
    lines = [
        f"🚨 <b>Nuevo Presupuesto Generado</b>",
        f"👤 <b>Vendedor:</b> {user['username']}",
        f"🏢 <b>Cliente:</b> {client_name}",
        f"💰 <b>Total:</b> ${total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        "",
        "📦 <b>Productos:</b>"
    ]
    
    for p in products:
        lines.append(f"• {p['name']} {p['unit']} - {p['quantity']}x = ${p['subtotal']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
    msg = "\n".join(lines)
    
    print("=== ENVIANDO A TELEGRAM ===")
    print(msg)
    print("===========================")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        fecha_emision = datetime.datetime.now().isoformat()
        tipo_comprobante = data.get("tipo_comprobante", "Presupuesto A")
        cliente_id = data.get("client_id", client_name) # Fallback to name if ID not provided
        
        cursor.execute('''
            INSERT INTO comprobantes (
                cliente_id, tipo_comprobante, fecha_emision,
                es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cliente_id, tipo_comprobante, fecha_emision,
            False, False, False, total, 0.0, total
        ))
        
        comprobante_id = cursor.lastrowid
        
        for p in products:
            cursor.execute('''
                INSERT INTO comprobantes_items (
                    comprobante_id, producto_id, descripcion, cantidad,
                    precio_unitario, alicuota_iva, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                comprobante_id, p.get("id", ""), p.get("name", ""), p.get("quantity", 0),
                p.get("price", 0), 0.0, p.get("subtotal", 0)
            ))
            
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print("Error guardando presupuesto en SQLite:", e)
        return {"error": str(e)}

@router.get("/api/cotizador/historial")
async def api_history_quotes(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, cliente_id, total, fecha_emision, tipo_comprobante
            FROM comprobantes
            WHERE tipo_comprobante LIKE 'Presupuesto%'
            ORDER BY id DESC
            LIMIT 50
        ''')
        rows = cursor.fetchall()
        
        history = []
        for r in rows:
            comp_id = r["id"]
            record = {
                "id": str(comp_id),
                "date": r["fecha_emision"],
                "seller": user["username"], # We don't have seller in comprobantes table currently, so we use current user or we could add it
                "client": r["cliente_id"],
                "total": r["total"],
                "tipo_comprobante": r["tipo_comprobante"],
                "tipoB": r["tipo_comprobante"] in ["Presupuesto B", "Factura B (Final / Interna)"]
            }
            
            # Fetch items
            cursor.execute('''
                SELECT producto_id as id, descripcion as name, cantidad as quantity, 
                       precio_unitario as price, subtotal, '' as unit
                FROM comprobantes_items
                WHERE comprobante_id = ?
            ''', (comp_id,))
            items = cursor.fetchall()
            record["products"] = [dict(item) for item in items]
            
            history.append(record)
            
        conn.close()
        return history
    except Exception as e:
        print("Error obteniendo historial de presupuestos:", e)
        return []

@router.delete("/api/cotizador/historial/{quote_id}")
async def api_delete_history_quote(quote_id: str, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM comprobantes_items WHERE comprobante_id = ?", (quote_id,))
        cursor.execute("DELETE FROM comprobantes WHERE id = ?", (quote_id,))
        
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print("Error eliminando presupuesto:", e)
        return {"error": str(e)}

@router.post("/api/generate-quote-pdf")
async def api_generate_quote_pdf(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    data = await request.json()
    client_name = data.get("client_name", "Consumidor Final")
    if not client_name.strip():
        client_name = "Consumidor Final"
        
    products = data.get("products", [])
    total = data.get("total", 0)
    tipo_comprobante = data.get("tipo_comprobante", "Presupuesto A")
    global_discount = data.get("globalDiscount", 0)
    iva_reducido = data.get("iva_reducido", False)
    
    quote_id = data.get("quote_id") or data.get("id")
    cae = data.get("cae")
    cae_vto = data.get("cae_vto")
    numero_afip = data.get("numero_afip")
    pto_vta = os.environ.get('AFIP_PTO_VTA', '10')
    
    if quote_id and not cae:
        db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT cae, cae_vto, numero_afip FROM comprobantes WHERE id = ?', (quote_id,))
            row = cursor.fetchone()
            if row and row[0]:
                cae, cae_vto, numero_afip = row
            conn.close()
        except:
            pass    
            
    # === OBTENER DIRECCIÓN COMPLETA ===
    cliente_id = data.get("client_id")
    if quote_id and not cliente_id:
        db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT cliente_id FROM comprobantes WHERE id = ?', (quote_id,))
            row = cursor.fetchone()
            if row and row[0]:
                cliente_id = row[0]
            conn.close()
        except:
            pass

    if cliente_id:
        db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT domicilio, localidad, provincia, razon_social FROM clientes WHERE id = ?', (cliente_id,))
            row = cursor.fetchone()
            if row:
                db_domicilio, db_localidad, db_provincia, db_razon_social = row
                full_address = db_domicilio or ""
                if db_localidad:
                    full_address += f" - {db_localidad}"
                if db_provincia:
                    full_address += f" ({db_provincia})"
                
                # Sobrescribimos o creamos el campo domicilio en el payload para que el PDF lo tome automáticamente
                data['cliente_domicilio'] = full_address.strip()
                
                if db_razon_social:
                    data['cliente_razon_social'] = db_razon_social
            conn.close()
        except Exception as e:
            print("Error fetching client complete address:", e)
    # ====================================

    original_date = data.get("date")
    if original_date:
        try:
            if 'T' in original_date or '-' in original_date:
                dt = datetime.datetime.fromisoformat(original_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%d/%m/%Y')
            else:
                date_str = original_date
        except:
            date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    else:
        date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e293b'),
        alignment=0,
        spaceAfter=0
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=5
    )
    
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    )

    tipo_upper = tipo_comprobante.upper()
    if "NOTA DE CRÉDITO" in tipo_upper:
        if " A" in tipo_upper and "INTERNA" not in tipo_upper:
            title_text = "NOTA DE CRÉDITO A"
            letter = "A"
        elif " B" in tipo_upper and "INTERNA" not in tipo_upper:
            title_text = "NOTA DE CRÉDITO B"
            letter = "B"
        else:
            title_text = "NOTA DE CRÉDITO INTERNA"
            letter = "X"
    elif "NOTA DE DÉBITO" in tipo_upper:
        if " A" in tipo_upper and "INTERNA" not in tipo_upper:
            title_text = "NOTA DE DÉBITO A"
            letter = "A"
        elif " B" in tipo_upper and "INTERNA" not in tipo_upper:
            title_text = "NOTA DE DÉBITO B"
            letter = "B"
        else:
            title_text = "NOTA DE DÉBITO INTERNA"
            letter = "X"
    elif tipo_comprobante == "Factura Electrónica A":
        letter = "A"
        title_text = "FACTURA A"
    elif tipo_comprobante == "Presupuesto A":
        letter = "P"
        title_text = "PRESUPUESTO"
    elif tipo_comprobante == "Factura Electrónica B":
        letter = "B"
        title_text = "FACTURA B"
    elif tipo_comprobante == "Factura B (Final / Interna)":
        letter = "B"
        title_text = "FACTURA B"
    elif tipo_comprobante == "Remito":
        letter = "R"
        title_text = "REMITO R"
    elif tipo_comprobante == "Recibo de Pago":
        letter = "X"
        title_text = "RECIBO DE PAGO X"
    else:
        letter = "P"
        title_text = "PRESUPUESTO"
        
    letter_table = Table([[Paragraph(f"<b>{letter}</b>", ParagraphStyle('L', fontSize=24, alignment=1))]], colWidths=[40], rowHeights=[40])
    letter_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 2, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    emisor_info = f"<b>{EMISOR_NOMBRE}</b><br/>Razón Social: {EMISOR_RAZON_SOCIAL} | CUIT: {EMISOR_CUIT}<br/>Condición de IVA: {EMISOR_CONDICION_IVA}<br/>Domicilio: {EMISOR_DOMICILIO}"
    left_cell = Paragraph(emisor_info, info_style)

    right_cell_text = f"<b>{title_text}</b><br/>"
    if numero_afip:
        right_cell_text += f"Nº {int(pto_vta):05d}-{int(numero_afip):08d}<br/>"
    right_cell_text += f"<b>Fecha:</b> {date_str}"
    right_cell = Paragraph(right_cell_text, ParagraphStyle('RightHeader', parent=info_style, alignment=2))
        
    header_table = Table([
        [left_cell, letter_table, right_cell]
    ], colWidths=[200, 100, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    cliente_info = f"<b>Cliente:</b> {client_name}"
    if data.get('cliente_razon_social'):
        cliente_info += f" | <b>Razón Social:</b> {data.get('cliente_razon_social')}"
    cliente_info += "<br/>"
    if data.get('cliente_cuit'):
        cliente_info += f"<b>CUIT / Doc:</b> {data.get('cliente_cuit')} | "
    if data.get('cliente_condicion_iva'):
        cliente_info += f"<b>Condición IVA:</b> {data.get('cliente_condicion_iva')}<br/>"
    if data.get('cliente_domicilio'):
        cliente_info += f"<b>Domicilio:</b> {data.get('cliente_domicilio')}<br/>"
    if data.get('cliente_telefono'):
        cliente_info += f"<b>Teléfono:</b> {data.get('cliente_telefono')}<br/>"
    cliente_info += f"<b>Vendedor:</b> {user['username'].capitalize()}"
    
    elements.append(Paragraph(cliente_info, info_style))
    elements.append(Spacer(1, 25))
    
    is_remito = tipo_comprobante == "Remito"
    is_recibo = tipo_comprobante == "Recibo de Pago"

    if is_recibo:
        table_data = [["Descripción", "Importe"]]
        colWidths = [380, 110]
    elif is_remito:
        table_data = [["Descripción", "Unidad", "Cant."]]
        colWidths = [320, 90, 80]
    else:
        table_data = [["Descripción", "Unidad", "Precio Unit.", "Desc.", "Cant.", "Subtotal"]]
        colWidths = [180, 60, 80, 40, 40, 90]
    
    is_tipo_b = False
    if " B" in tipo_comprobante or "Interna" in tipo_comprobante or "Presupuesto B" in tipo_comprobante:
        is_tipo_b = True
        
    multiplier = 1.0

    for p in products:
        if is_recibo:
            amount = p.get('subtotal', p.get('price', 0))
            amount_str = f"$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            desc_para = Paragraph(p['name'], cell_style)
            table_data.append([desc_para, amount_str])
        elif is_remito:
            desc_para = Paragraph(p['name'], cell_style)
            table_data.append([desc_para, p['unit'], str(p['quantity'])])
        else:
            price = p['price'] * multiplier
            subtotal = p['subtotal'] * multiplier
            
            desc_para = Paragraph(p['name'], cell_style)
            price_str = f"$ {price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            subtotal_str = f"$ {subtotal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            discount_str = f"{p.get('discount', 0)}%" if p.get('discount', 0) > 0 else "-"
            
            table_data.append([
                desc_para, 
                p['unit'], 
                price_str,
                discount_str,
                str(p['quantity']), 
                subtotal_str
            ])
        
    t = Table(table_data, colWidths=colWidths)
    
    if is_recibo:
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ]
    elif is_remito:
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (2,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ]
    else:
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'LEFT'),
            ('ALIGN', (2,0), (5,-1), 'RIGHT'),
            ('ALIGN', (3,0), (4,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ]
        
    t.setStyle(TableStyle(t_style))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    if global_discount > 0:
        elements.append(Paragraph(f"<b>Descuento especial aplicado: {global_discount}%</b>", info_style))
        elements.append(Spacer(1, 10))
    
    display_total = total * multiplier
    total_str = f"$ {display_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#1e293b'),
        alignment=2 
    )
    
    if is_remito:
        pass # Remito doesn't show totals
    elif is_recibo:
        elements.append(Paragraph(f"<b>Total: {total_str}</b>", total_style))
    elif is_tipo_b:
        elements.append(Paragraph(f"<b>Total (Final): {total_str}</b>", total_style))
        if tipo_comprobante == "Factura Electrónica B":
            # IVA Contenido
            # Prompt: "Solo Factura Electrónica B dice 'IVA Contenido: $...' (calculado al 21%)."
            base_total_21 = display_total / 1.21
            iva_contenido = display_total - base_total_21
            iva_cont_str = f"$ {iva_contenido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            sub_style = ParagraphStyle('SubTotal', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#475569'), alignment=2)
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"IVA Contenido: {iva_cont_str}", sub_style))
    else:
        elements.append(Paragraph(f"<b>Total Estimado (+ IVA 21%): {total_str}</b>", total_style))
        
        iva_amount = display_total * 0.21
        total_with_iva = display_total * 1.21
        
        iva_str = f"$ {iva_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        total_with_iva_str = f"$ {total_with_iva:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        sub_style = ParagraphStyle(
            'SubTotal',
            parent=styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#475569'),
            alignment=2
        )
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"IVA (21%): {iva_str}", sub_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"<b>Total con IVA: {total_with_iva_str}</b>", total_style))

    if cae:
        import afip_service
        from reportlab.platypus import Image
        
        doc_nro = int(data.get("client_id", "0")) if str(data.get("client_id", "")).isdigit() else 0
        if doc_nro > 0:
            doc_tipo = 80 if len(str(doc_nro)) == 11 else 96
        else:
            doc_tipo = 99
            doc_nro = 0
            
        tipo_cbte = 1 if tipo_comprobante == "Factura Electrónica A" else 6
        
        try:
            qr_bytes = afip_service.generar_qr_afip(
                cae=cae,
                numero_afip=numero_afip,
                pto_vta=int(pto_vta),
                doc_tipo=doc_tipo,
                doc_nro=doc_nro,
                tipo_cbte=tipo_cbte,
                fecha=datetime.datetime.now().strftime("%Y-%m-%d"),
                total=display_total
            )
            img = Image(io.BytesIO(qr_bytes), width=100, height=100)
        except Exception as e:
            print("Error generando QR:", e)
            img = Paragraph("QR no disponible", info_style)
        
        cae_style = ParagraphStyle('CAE', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'))
        footer_table = Table([
            [img, Paragraph(f"<b>CAE:</b> {cae}<br/><b>Vto CAE:</b> {cae_vto}", cae_style)]
        ], colWidths=[110, 300])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elements.append(Spacer(1, 20))
        elements.append(footer_table)

    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Presupuesto_Disgraf.pdf"})

