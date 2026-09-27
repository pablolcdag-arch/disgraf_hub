from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import sqlite3
import os
from dependencies import get_current_user, DATA_DIR

router = APIRouter()

class ComprobanteItem(BaseModel):
    producto_id: str
    descripcion: str
    cantidad: float
    precio_unitario: float
    alicuota_iva: float
    subtotal: float

class ComprobanteCreate(BaseModel):
    cliente_id: str
    tipo_comprobante: str # "Factura Electrónica A", "Factura Electrónica B", "Factura B (Final / Interna)", "Presupuesto"
    numero_comprobante: Optional[str] = None
    fecha_emision: Optional[str] = None
    subtotal: float
    total_iva: float
    total: float
    items: List[ComprobanteItem]
    iva_reducido: bool = False
    comprobante_asociado_id: Optional[int] = None
    facturar_afip: Optional[bool] = False

import afip_service

@router.post("/api/ventas/comprobantes")
async def crear_comprobante(comprobante: ComprobanteCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    es_fiscal = False
    impacta_cc = False
    impacta_stock = False
    total_iva = comprobante.total_iva

    if comprobante.tipo_comprobante.startswith("Nota de Débito") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="No tenés permiso para crear Notas de Débito")

    if comprobante.tipo_comprobante.startswith("Presupuesto"):
        es_fiscal = False
        impacta_cc = False
        impacta_stock = False
    elif comprobante.tipo_comprobante == "Factura B (Final / Interna)":
        es_fiscal = False
        impacta_cc = True
        impacta_stock = True
        total_iva = 0.0
    elif comprobante.tipo_comprobante in ["Factura Electrónica A", "Factura Electrónica B"]:
        es_fiscal = True
        impacta_cc = True
        impacta_stock = True
    elif comprobante.tipo_comprobante.startswith("Nota de Crédito"):
        impacta_cc = True
        impacta_stock = True
        es_fiscal = (comprobante.tipo_comprobante.endswith("A") or comprobante.tipo_comprobante.endswith("B")) and "Interna" not in comprobante.tipo_comprobante
    elif comprobante.tipo_comprobante.startswith("Nota de Débito"):
        impacta_cc = True
        impacta_stock = False
        es_fiscal = (comprobante.tipo_comprobante.endswith("A") or comprobante.tipo_comprobante.endswith("B")) and "Interna" not in comprobante.tipo_comprobante
    elif comprobante.tipo_comprobante == "Remito":
        impacta_stock = False
        impacta_cc = False
        es_fiscal = False
    elif comprobante.tipo_comprobante == "Recibo de Pago":
        impacta_stock = False
        impacta_cc = True
        es_fiscal = False
    else:
        # Default or fallback
        pass

    fecha_emision = comprobante.fecha_emision or str(date.today())

    cae = None
    cae_vto = None
    numero_afip = None

    if comprobante.facturar_afip:
        try:
            afip_res = afip_service.emitir_factura(
                cliente_nro=comprobante.cliente_id,
                total=comprobante.total,
                tipo_factura=comprobante.tipo_comprobante,
                iva_reducido=comprobante.iva_reducido
            )
            cae = afip_res['cae']
            cae_vto = afip_res['cae_vto']
            numero_afip = afip_res['numero_afip']
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error en AFIP: {str(e)}")

    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO comprobantes (
                cliente_id, tipo_comprobante, numero_comprobante, fecha_emision,
                es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total,
                comprobante_asociado_id, cae, cae_vto, numero_afip
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comprobante.cliente_id, comprobante.tipo_comprobante, comprobante.numero_comprobante,
            fecha_emision, es_fiscal, impacta_cc, impacta_stock, comprobante.subtotal, total_iva, comprobante.total,
            comprobante.comprobante_asociado_id, cae, cae_vto, numero_afip
        ))
        
        comprobante_id = cursor.lastrowid

        for item in comprobante.items:
            cursor.execute('''
                INSERT INTO comprobantes_items (
                    comprobante_id, producto_id, descripcion, cantidad,
                    precio_unitario, alicuota_iva, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                comprobante_id, item.producto_id, item.descripcion, item.cantidad,
                item.precio_unitario, item.alicuota_iva, item.subtotal
            ))

        conn.commit()
        conn.close()

        return {"id": comprobante_id, "message": "Comprobante creado exitosamente"}
    except Exception as e:
        print("Error creando comprobante:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/ventas/cliente/{cliente_id}")
async def get_cliente_comprobantes(cliente_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, cliente_id, tipo_comprobante, numero_comprobante, fecha_emision,
                   es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total,
                   estado, comprobante_asociado_id, cae, cae_vto, numero_afip
            FROM comprobantes
            WHERE cliente_id = ?
            ORDER BY fecha_emision DESC, id DESC
        ''', (cliente_id,))
        
        rows = cursor.fetchall()
        comprobantes = [dict(row) for row in rows]
        
        conn.close()
        return comprobantes
    except Exception as e:
        print("Error obteniendo comprobantes del cliente:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/ventas/comprobante/{id}")
async def get_comprobante(id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, cliente_id, tipo_comprobante, numero_comprobante, fecha_emision,
                   es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total,
                   estado, comprobante_asociado_id, cae, cae_vto, numero_afip
            FROM comprobantes
            WHERE id = ?
        ''', (id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Comprobante no encontrado")
            
        comprobante = dict(row)
        
        cursor.execute('''
            SELECT id, comprobante_id, producto_id, descripcion, cantidad,
                   precio_unitario, alicuota_iva, subtotal
            FROM comprobantes_items
            WHERE comprobante_id = ?
        ''', (id,))
        
        items_rows = cursor.fetchall()
        comprobante["items"] = [dict(item) for item in items_rows]
        
        conn.close()
        return comprobante
    except HTTPException:
        raise
    except Exception as e:
        print("Error obteniendo comprobante:", e)
        raise HTTPException(status_code=500, detail=str(e))


class AjusteSaldoPayload(BaseModel):
    cliente_id: str
    monto: float
    concepto: str

@router.post("/api/ventas/ajuste-saldo")
async def ajuste_saldo(payload: AjusteSaldoPayload, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar ajustes de saldo")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        fecha_emision = str(date.today())
        
        cursor.execute('''
            INSERT INTO comprobantes (
                cliente_id, tipo_comprobante, fecha_emision,
                es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payload.cliente_id, "Ajuste de Saldo", fecha_emision,
            False, True, False, payload.monto, 0.0, payload.monto
        ))
        
        comprobante_id = cursor.lastrowid
        
        # Opcional: Insertar un item en comprobantes_items para detallar el concepto
        cursor.execute('''
            INSERT INTO comprobantes_items (
                comprobante_id, producto_id, descripcion, cantidad,
                precio_unitario, alicuota_iva, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            comprobante_id, "AJUSTE", payload.concepto, 1,
            payload.monto, 0.0, payload.monto
        ))
        
        conn.commit()
        conn.close()
        
        return {"id": comprobante_id, "message": "Ajuste de saldo registrado exitosamente"}
    except Exception as e:
        print("Error en ajuste de saldo:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/reportes/dashboard")
async def reportes_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder a los reportes")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        fecha_hoy = str(date.today())
        
        # Ventas de hoy
        cursor.execute('''
            
            SELECT 
                SUM(CASE WHEN tipo_comprobante LIKE 'Factura%' OR tipo_comprobante LIKE 'Recibo%' THEN total 
                         WHEN tipo_comprobante LIKE 'Nota de Cr_dito%' THEN -total 
                         ELSE 0 END) as suma
            FROM comprobantes
            WHERE fecha_emision = ? 

        ''', (fecha_hoy,))
        row_hoy = cursor.fetchone()
        ventas_hoy = row_hoy['suma'] if row_hoy and row_hoy['suma'] else 0.0
        
        # Ventas de la semana (últimos 7 días)
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN tipo_comprobante LIKE 'Factura%' OR tipo_comprobante LIKE 'Recibo%' THEN total 
                         WHEN tipo_comprobante LIKE 'Nota de Cr_dito%' THEN -total 
                         ELSE 0 END) as suma
            FROM comprobantes
            WHERE fecha_emision >= date('now', '-7 days') 
        ''')
        row_semana = cursor.fetchone()
        ventas_semana = row_semana['suma'] if row_semana and row_semana['suma'] else 0.0
        
        # Ventas del mes (últimos 30 días)
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN tipo_comprobante LIKE 'Factura%' OR tipo_comprobante LIKE 'Recibo%' THEN total 
                         WHEN tipo_comprobante LIKE 'Nota de Cr_dito%' THEN -total 
                         ELSE 0 END) as suma
            FROM comprobantes
            WHERE fecha_emision >= date('now', '-30 days') 
        ''')
        row_mes = cursor.fetchone()
        ventas_mes = row_mes['suma'] if row_mes and row_mes['suma'] else 0.0
        
        # Cantidad de facturas emitidas
        cursor.execute('''
            SELECT COUNT(*) as cantidad
            FROM comprobantes
            WHERE tipo_comprobante LIKE 'Factura%'
        ''')
        row_facturas = cursor.fetchone()
        cantidad_facturas = row_facturas['cantidad'] if row_facturas else 0
        
        # Últimos 5 presupuestos
        cursor.execute('''
            SELECT id, cliente_id, total, fecha_emision
            FROM comprobantes
            WHERE tipo_comprobante LIKE 'Presupuesto%'
            ORDER BY fecha_emision DESC, id DESC
            LIMIT 5
        ''')
        rows_presupuestos = cursor.fetchall()
        ultimos_presupuestos = [dict(r) for r in rows_presupuestos]
        
        conn.close()
        
        return {
            "ventas_hoy": ventas_hoy,
            "ventas_semana": ventas_semana,
            "ventas_mes": ventas_mes,
            "cantidad_facturas": cantidad_facturas,
            "ultimos_presupuestos": ultimos_presupuestos
        }
    except Exception as e:
        print("Error generando reportes dashboard:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/reportes/auditoria")
async def reportes_auditoria(
    request: Request,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo_comprobante: Optional[str] = None
):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder a los reportes")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM comprobantes WHERE 1=1"
        params = []
        
        if fecha_desde:
            query += " AND fecha_emision >= ?"
            params.append(fecha_desde)
            
        if fecha_hasta:
            query += " AND fecha_emision <= ?"
            params.append(fecha_hasta)
            
        if tipo_comprobante:
            query += " AND tipo_comprobante LIKE ?"
            params.append(tipo_comprobante + "%")
            
        query += " ORDER BY fecha_emision DESC, id DESC LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        comprobantes = [dict(r) for r in rows]
        conn.close()
        
        return {"comprobantes": comprobantes}
    except Exception as e:
        print("Error generando reporte auditoria:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/reportes/deudores")
async def reportes_deudores(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder a los reportes")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                cliente_id,
                SUM(
                    CASE 
                        WHEN tipo_comprobante LIKE 'Factura%' OR tipo_comprobante LIKE 'Nota de Débito%' THEN total
                        WHEN tipo_comprobante LIKE 'Recibo%' OR tipo_comprobante LIKE 'Nota de Crédito%' THEN -total
                        WHEN tipo_comprobante = 'Ajuste de Saldo' THEN -total
                        ELSE 0
                    END
                ) as saldo
            FROM comprobantes
            WHERE impacta_cc = 1
            GROUP BY cliente_id
            HAVING saldo > 1
            ORDER BY saldo DESC
        ''')
        
        rows = cursor.fetchall()
        deudores = [dict(r) for r in rows]
        
        conn.close()
        
        return {"deudores": deudores}
    except Exception as e:
        print("Error generando reporte deudores:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/ventas/comprobante/{id}")
async def delete_comprobante(id: int, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT cae FROM comprobantes WHERE id = ?", (id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Comprobante no encontrado")

        if row["cae"]:
            conn.close()
            raise HTTPException(status_code=403, detail="No se puede eliminar un comprobante emitido en AFIP.")

        cursor.execute("DELETE FROM comprobantes_items WHERE comprobante_id = ?", (id,))
        cursor.execute("DELETE FROM comprobantes WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        print("Error eliminando comprobante:", e)
        raise HTTPException(status_code=500, detail=str(e))
