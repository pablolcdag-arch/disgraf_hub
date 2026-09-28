import sqlite3
import os

DB_PATH = '/opt/disgraf_hub/data/disgraf_hub.db'

def run():
    print(f"Migrando {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS comprobantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        tipo_comprobante TEXT,
        numero_comprobante TEXT,
        fecha_emision DATE,
        es_fiscal BOOLEAN,
        impacta_cc BOOLEAN,
        impacta_stock BOOLEAN,
        subtotal REAL,
        total_iva REAL,
        total REAL,
        estado TEXT DEFAULT 'Emitido',
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS comprobantes_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comprobante_id INTEGER,
        producto_id TEXT,
        descripcion TEXT,
        cantidad REAL,
        precio_unitario REAL,
        alicuota_iva REAL,
        subtotal REAL,
        FOREIGN KEY(comprobante_id) REFERENCES comprobantes(id)
    )
    ''')
    conn.commit()
    conn.close()
    print("Migración de comprobantes completada con éxito.")

if __name__ == '__main__':
    run()
