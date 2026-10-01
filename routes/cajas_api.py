import os
import sqlite3
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from pydantic import BaseModel
from dependencies import get_current_user

router = APIRouter()
DATA_DIR = os.environ.get("DATA_DIR", "./data")

class MovimientoCreate(BaseModel):
    caja_id: int
    tipo: str  # 'ingreso' o 'egreso'
    monto: float
    concepto: str
    caja_destino_id: Optional[int] = None

@router.get("/api/cajas")
async def get_cajas(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.nombre,
               COALESCE(SUM(CASE WHEN m.tipo='ingreso' THEN m.monto ELSE -m.monto END), 0) as saldo
        FROM cajas c
        LEFT JOIN cajas_movimientos m ON c.id = m.caja_id
        GROUP BY c.id
    ''')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@router.get("/api/cajas/{id}/movimientos")
async def get_caja_movimientos(id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM cajas_movimientos WHERE caja_id = ? ORDER BY id DESC',
        (id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@router.post("/api/cajas/movimiento")
async def crear_movimiento(mov: MovimientoCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    role = user.get("role")
    if role == "seller":
        if mov.tipo.lower() != "egreso":
            raise HTTPException(status_code=403, detail="Los vendedores solo tienen permiso para registrar egresos.")
    elif role != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden crear movimientos manuales")
        
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cajas_movimientos (caja_id, tipo, monto, usuario, concepto)
        VALUES (?, ?, ?, ?, ?)
    ''', (mov.caja_id, mov.tipo.lower(), mov.monto, user['username'], mov.concepto))
    conn.commit()
    conn.close()
    return {"status": "success"}

