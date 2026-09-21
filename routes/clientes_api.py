from fastapi import APIRouter, Request
from dependencies import get_current_user, DATA_DIR
import os
import json
import sqlite3

router = APIRouter()
@router.get("/api/clientes/buscar")
async def api_buscar_clientes(q: str = "", limit: int = 10, request: Request = None):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import sqlite3
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

@router.get("/api/clientes/{client_id}")
async def api_get_cliente(client_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import sqlite3
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
        
    import json
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
