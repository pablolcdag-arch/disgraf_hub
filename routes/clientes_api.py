from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from dependencies import get_current_user, DATA_DIR
from pydantic import BaseModel
from typing import Optional
import os
import json
import sqlite3
import csv
import io

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
