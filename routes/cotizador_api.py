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

router = APIRouter()

@router.post("/api/log-quote")
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
        
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    history_data = []
    
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except:
            pass
            
    new_record = {
        "id": str(uuid.uuid4())[:8],
        "date": datetime.datetime.now().isoformat(),
        "seller": user["username"],
        "client": client_name,
        "client_id": data.get("client_id"),
        "total": total,
        "products": products,
        "tipo_comprobante": data.get("tipo_comprobante", "Presupuesto A"),
        "iva_reducido": data.get("iva_reducido", False),
        "tipoB": data.get("tipo_comprobante", "Presupuesto A") in ["Presupuesto B", "Factura B (Final / Interna)"]
    }
    history_data.insert(0, new_record)
    
    ten_days_ago = datetime.datetime.now() - datetime.timedelta(days=10)
    valid_history = []
    for r in history_data:
        try:
            r_date = datetime.datetime.fromisoformat(r["date"])
            if r_date >= ten_days_ago:
                valid_history.append(r)
        except:
            pass
            
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(valid_history, f, ensure_ascii=False, indent=2)
        
    return {"status": "success"}

@router.get("/api/history-quotes")
async def api_history_quotes(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

@router.delete("/api/history-quotes/{quote_id}")
async def api_delete_history_quote(quote_id: str, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if not os.path.exists(history_path):
        return {"error": "History file not found"}
        
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        new_history = [q for q in history if q.get("id") != quote_id]
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
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

    if tipo_comprobante == "Factura Electrónica A":
        letter = "A"
        title_text = "FACTURA A"
    elif tipo_comprobante == "Presupuesto A":
        letter = "P"
        title_text = "PRESUPUESTO"
    elif tipo_comprobante == "Factura Electrónica B":
        letter = "B"
        title_text = "FACTURA B"
    else:
        letter = "P"
        title_text = "PRESUPUESTO"
        
    letter_table = Table([[Paragraph(f"<b>{letter}</b>", ParagraphStyle('L', fontSize=24, alignment=1))]], colWidths=[40], rowHeights=[40])
    letter_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 2, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    header_table = Table([
        [Paragraph(f"<b>{title_text}</b>", title_style), letter_table, Paragraph(f"<b>Fecha:</b> {datetime.datetime.now().strftime('%d/%m/%Y')}", info_style)]
    ], colWidths=[200, 100, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Cliente:</b> {client_name}", info_style))
    elements.append(Paragraph(f"<b>Vendedor:</b> {user['username'].capitalize()}", info_style))
    elements.append(Spacer(1, 25))
    
    table_data = [["Descripción", "Unidad", "Precio Unit.", "Desc.", "Cant.", "Subtotal"]]
    
    multiplier = 1.0
    if tipo_comprobante in ["Factura Electrónica B", "Factura B (Final / Interna)", "Presupuesto B"]:
        multiplier = 1.105 if iva_reducido else 1.21

    for p in products:
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
        
    t = Table(table_data, colWidths=[180, 60, 80, 40, 40, 90])
    t.setStyle(TableStyle([
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
    ]))
    
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
    
    if tipo_comprobante in ["Factura Electrónica B", "Factura B (Final / Interna)", "Presupuesto B"]:
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

    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Presupuesto_Disgraf.pdf"})

