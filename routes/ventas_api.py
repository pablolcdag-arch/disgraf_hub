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

    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO comprobantes (
                cliente_id, tipo_comprobante, numero_comprobante, fecha_emision,
                es_fiscal, impacta_cc, impacta_stock, subtotal, total_iva, total,
                comprobante_asociado_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comprobante.cliente_id, comprobante.tipo_comprobante, comprobante.numero_comprobante,
            fecha_emision, es_fiscal, impacta_cc, impacta_stock, comprobante.subtotal, total_iva, comprobante.total,
            comprobante.comprobante_asociado_id
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
                   estado, comprobante_asociado_id
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
                   estado, comprobante_asociado_id
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

