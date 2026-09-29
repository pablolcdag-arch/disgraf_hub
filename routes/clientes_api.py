from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from dependencies import get_current_user, DATA_DIR
from pydantic import BaseModel
from typing import Optional
import os
import json
import sqlite3
import csv
import io
from fastapi.responses import Response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import datetime

router = APIRouter()

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    estado: Optional[str] = None
    contacto: Optional[str] = None
    telefonos: Optional[str] = None
    domicilio: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    mail: Optional[str] = None
    condicion_iva: Optional[str] = None
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    documento: Optional[str] = None
    otro_tipo_documento: Optional[str] = None
    moneda: Optional[str] = None
    observaciones: Optional[str] = None
    observaciones_internas: Optional[str] = None
    recordatorio: Optional[str] = None
    codigo_postal: Optional[str] = None
    lista_de_precio: Optional[str] = None
    permite_cuenta_corriente: Optional[bool] = None
    limite_cuenta_corriente: Optional[float] = None

class ClienteCreate(ClienteUpdate):
    nombre: str

@router.get("/api/clientes/buscar")
async def api_buscar_clientes(q: str = "", limit: int = 10, request: Request = None):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    if not os.path.exists(db_path):
        return []
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f"%{q}%"
        cursor.execute('''
            SELECT id, nombre, contacto, condicion_iva, cuit 
            FROM clientes 
            WHERE nombre LIKE ? OR cuit LIKE ? OR razon_social LIKE ?
            LIMIT ?
        ''', (query, query, query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print("Error buscando clientes:", e)
        return []

@router.get("/api/clientes/export")
async def export_clientes(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes")
        rows = cursor.fetchall()
        conn.close()
        
        output = io.StringIO()
        if rows:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        else:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(["No hay clientes"])
            
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clientes_disgraf.csv"}
        )
    except Exception as e:
        print("Error exportando clientes:", e)
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/api/clientes/{client_id}")
async def api_get_cliente(client_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return {"error": "Cliente no encontrado"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/clientes/{client_id}/presupuestos")
async def api_get_cliente_presupuestos(client_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if not os.path.exists(history_path):
        return []
        
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        client_history = [q for q in history if str(q.get("client_id")) == str(client_id)]
        return client_history
    except:
        return []

@router.post("/api/clientes/importar")
async def importar_clientes(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Solo admin puede importar? Asumimos que sí, o vendedores también pueden? 
    # El prompt no lo restringe explícitamente pero tiene sentido que vendedores no importen bases enteras, 
    # aunque no dice nada en particular. Dejemos que pase si está autorizado.
    
    contents = await file.read()
    
    # Try different encodings
    try:
        text = contents.decode('utf-8')
    except UnicodeDecodeError:
        text = contents.decode('latin-1')

    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read CSV
        csv_reader = csv.DictReader(io.StringIO(text), delimiter=';')
        
        count_insert = 0
        count_update = 0
        
        for row in csv_reader:
            client_id_str = row.get("Nº de cliente")
            if not client_id_str:
                continue
                
            try:
                client_id = int(client_id_str)
            except ValueError:
                continue
                
            categoria = row.get("Categoría del cliente", "")
            estado = row.get("Estado", "")
            nombre = row.get("Nombre", "")
            contacto = row.get("Contacto", "")
            telefonos = row.get("Teléfonos", "")
            domicilio = row.get("Domicilio", "")
            localidad = row.get("Localidad", "")
            provincia = row.get("Provincia", "")
            mail = row.get("Mail", "")
            condicion_iva = row.get("Condición de IVA", "")
            razon_social = row.get("Razón Social", "")
            cuit = row.get("CUIT", "")
            documento = row.get("N° de documento", "")
            otro_tipo_documento = row.get("Otro tipo de documento", "")
            moneda = row.get("Moneda", "Pesos")
            observaciones = row.get("Observaciones", "")
            observaciones_internas = row.get("Observaciones Internas", "")
            recordatorio = row.get("Recordatorio", "")
            codigo_postal = row.get("Codigo Postal", "")
            lista_de_precio = "Lista 1"
            permite_cuenta_corriente = False
            limite_cuenta_corriente = 0.0
            
            # Check if exists
            cursor.execute("SELECT id FROM clientes WHERE id = ?", (client_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE clientes SET
                        categoria = ?, estado = ?, nombre = ?, contacto = ?, telefonos = ?,
                        domicilio = ?, localidad = ?, provincia = ?, mail = ?, condicion_iva = ?,
                        razon_social = ?, cuit = ?, documento = ?, otro_tipo_documento = ?,
                        moneda = ?, observaciones = ?, observaciones_internas = ?, recordatorio = ?,
                        codigo_postal = ?
                    WHERE id = ?
                ''', (categoria, estado, nombre, contacto, telefonos, domicilio, localidad, provincia, 
                      mail, condicion_iva, razon_social, cuit, documento, otro_tipo_documento, 
                      moneda, observaciones, observaciones_internas, recordatorio, codigo_postal, 
                      client_id))
                count_update += 1
            else:
                cursor.execute('''
                    INSERT INTO clientes (
                        id, categoria, estado, nombre, contacto, telefonos, domicilio, 
                        localidad, provincia, mail, condicion_iva, razon_social, cuit, 
                        documento, otro_tipo_documento, moneda, observaciones, observaciones_internas, 
                        recordatorio, codigo_postal, lista_de_precio, permite_cuenta_corriente, limite_cuenta_corriente
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (client_id, categoria, estado, nombre, contacto, telefonos, domicilio, 
                      localidad, provincia, mail, condicion_iva, razon_social, cuit, 
                      documento, otro_tipo_documento, moneda, observaciones, observaciones_internas, 
                      recordatorio, codigo_postal, lista_de_precio, permite_cuenta_corriente, limite_cuenta_corriente))
                count_insert += 1
                
        conn.commit()
        conn.close()
        
        return {"message": f"Importación exitosa. {count_insert} nuevos, {count_update} actualizados."}
    except Exception as e:
        print("Error en importacion:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/clientes")
async def create_cliente(cliente: ClienteCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # We don't insert id, it auto-increments
        cursor.execute('''
            INSERT INTO clientes (
                nombre, categoria, estado, contacto, telefonos, domicilio, 
                localidad, provincia, mail, condicion_iva, razon_social, cuit, 
                documento, otro_tipo_documento, moneda, observaciones, observaciones_internas, 
                recordatorio, codigo_postal, lista_de_precio, permite_cuenta_corriente, limite_cuenta_corriente
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cliente.nombre, cliente.categoria, cliente.estado, cliente.contacto, cliente.telefonos, cliente.domicilio,
            cliente.localidad, cliente.provincia, cliente.mail, cliente.condicion_iva, cliente.razon_social, cliente.cuit,
            cliente.documento, cliente.otro_tipo_documento, cliente.moneda, cliente.observaciones, cliente.observaciones_internas,
            cliente.recordatorio, cliente.codigo_postal, cliente.lista_de_precio, cliente.permite_cuenta_corriente, cliente.limite_cuenta_corriente
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return {"id": new_id, "message": "Cliente creado exitosamente"}
    except Exception as e:
        print("Error creando cliente:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/clientes/{client_id}")
async def update_cliente(client_id: int, cliente: ClienteUpdate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        cliente_dict = cliente.model_dump(exclude_unset=True)
        
        if not cliente_dict:
            return {"message": "No hay campos para actualizar"}
            
        for key, value in cliente_dict.items():
            update_fields.append(f"{key} = ?")
            values.append(value)
            
        values.append(client_id)
        
        query = f"UPDATE clientes SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor.execute(query, tuple(values))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
        conn.close()
        
        return {"message": "Cliente actualizado exitosamente"}
    except Exception as e:
        print("Error actualizando cliente:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/clientes")
async def api_get_all_clientes(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, razon_social FROM clientes")
        rows = cursor.fetchall()
        conn.close()
        
        return {"clientes": [dict(r) for r in rows]}
    except Exception as e:
        return {"error": str(e)}

EMISOR_NOMBRE = os.environ.get("EMISOR_NOMBRE", "DISGRAF Insumos Gráficos")
EMISOR_CUIT = os.environ.get("EMISOR_CUIT", "20-30254446-9")
EMISOR_CONDICION_IVA = os.environ.get("EMISOR_CONDICION_IVA", "IVA Responsable Inscripto")
EMISOR_DOMICILIO = os.environ.get("EMISOR_DOMICILIO", "Dr. Juan Felipe Aranguren 49 CABA")

@router.get("/api/clientes/{client_id}/cuenta_corriente/pdf")
async def api_get_cuenta_corriente_pdf(client_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener datos del cliente
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (client_id,))
        cliente_row = cursor.fetchone()
        if not cliente_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        cliente = dict(cliente_row)
        
        # Obtener comprobantes de la cuenta corriente
        cursor.execute('''
            SELECT fecha_emision, tipo_comprobante, id, total 
            FROM comprobantes 
            WHERE cliente_id = ? AND impacta_cc = 1 
            ORDER BY fecha_emision ASC
        ''', (client_id,))
        comprobantes = cursor.fetchall()
        conn.close()
        
        # Generar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=1.5*28.34, leftMargin=1.5*28.34,
                                topMargin=1.5*28.34, bottomMargin=1.5*28.34)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=15,
            alignment=1
        )
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155'),
            leading=14
        )
        
        # Encabezado Emisor
        emisor_info = f"""
        <b>{EMISOR_NOMBRE}</b><br/>
        <b>CUIT:</b> {EMISOR_CUIT}<br/>
        <b>Condición IVA:</b> {EMISOR_CONDICION_IVA}<br/>
        <b>Domicilio:</b> {EMISOR_DOMICILIO}
        """
        
        # Encabezado Cliente
        cliente_cuit = cliente.get('cuit')
        if not cliente_cuit or cliente_cuit == '0':
            cliente_cuit = cliente.get('documento', '')
            
        cliente_info = f"""
        <b>Cliente:</b> {cliente.get('nombre', '')}<br/>
        <b>CUIT / Doc:</b> {cliente_cuit} | 
        <b>Condición IVA:</b> {cliente.get('condicion_iva', 'Consumidor Final')}<br/>
        <b>Domicilio:</b> {cliente.get('domicilio', '')} {cliente.get('localidad', '')}
        """
        
        header_table = Table([
            [Paragraph(emisor_info, info_style), Paragraph(cliente_info, info_style)]
        ], colWidths=[240, 240])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("Resumen de Cuenta Corriente", title_style))
        elements.append(Spacer(1, 10))
        
        # Tabla de Movimientos
        table_data = [["Fecha", "Comprobante", "Debe", "Haber", "Saldo"]]
        saldo = 0.0
        
        for c in comprobantes:
            tipo = c['tipo_comprobante'] or ""
            total = float(c['total'] or 0)
            
            fecha_str = ""
            if c['fecha_emision']:
                try:
                    fecha_obj = datetime.datetime.fromisoformat(c['fecha_emision'])
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_str = str(c['fecha_emision'])[:10]
            
            debe = 0.0
            haber = 0.0
            
            if "Factura" in tipo or "Nota de Débito" in tipo or "Presupuesto" in tipo:
                debe = total
                saldo += total
            elif "Recibo" in tipo or "Nota de Crédito" in tipo:
                haber = total
                saldo -= total
            elif "Ajuste de Saldo" in tipo:
                if total >= 0:
                    debe = total
                else:
                    haber = abs(total)
                saldo += total
            
            debe_str = f"$ {debe:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if debe > 0 else ""
            haber_str = f"$ {haber:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if haber > 0 else ""
            saldo_str = f"$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            comp_name = f"{tipo} Nº {c['id']}"
            
            table_data.append([fecha_str, Paragraph(comp_name, info_style), debe_str, haber_str, saldo_str])
        
        t = Table(table_data, colWidths=[70, 170, 85, 85, 90])
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            
            ('ALIGN', (0,1), (0,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ]
        t.setStyle(TableStyle(t_style))
        elements.append(t)
        
        doc.build(elements)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Cuenta_Corriente_Cliente{client_id}.pdf"}
        )
        
    except Exception as e:
        print("Error generando PDF CC:", e)
        raise HTTPException(status_code=500, detail=str(e))

