import sqlite3

def fix_clientes_db():
    conn = sqlite3.connect("data/disgraf_hub.db")
    cursor = conn.cursor()
    
    # Obtener TODOS los comprobantes cuyo cliente_id contiene letras (es texto, no ID)
    cursor.execute("SELECT id, cliente_id FROM comprobantes WHERE cliente_id GLOB '*[A-Za-z]*'")
    comprobantes = cursor.fetchall()
    
    for cbte in comprobantes:
        cbte_id, cliente_texto = cbte
        # Buscar el ID real del cliente (sin importar mayúsculas/minúsculas)
        cursor.execute("SELECT id FROM clientes WHERE nombre COLLATE NOCASE = ? OR razon_social COLLATE NOCASE = ?", (cliente_texto, cliente_texto))
        match = cursor.fetchone()
        
        if match:
            real_id = match[0]
            cursor.execute("UPDATE comprobantes SET cliente_id = ? WHERE id = ?", (str(real_id), cbte_id))
            print(f"✅ Comprobante {cbte_id} corregido: de '{cliente_texto}' a ID real {real_id}")
        else:
            print(f"⚠️ Comprobante {cbte_id}: cliente '{cliente_texto}' no se encontró en la BD.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_clientes_db()

