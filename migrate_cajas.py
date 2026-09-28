import sqlite3
import os

def migrate_cajas():
    data_dir = os.environ.get('DATA_DIR', './data')
    db_path = os.path.join(data_dir, 'disgraf_hub.db')
    
    print(f"Conectando a la base de datos en: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creando tabla cajas...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cajas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    );
    ''')
    
    print("Creando tabla cajas_movimientos...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cajas_movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caja_id INTEGER NOT NULL,
        tipo TEXT NOT NULL, -- 'Ingreso' o 'Egreso'
        monto REAL NOT NULL,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT,
        concepto TEXT,
        comprobante_id INTEGER DEFAULT NULL,
        FOREIGN KEY (caja_id) REFERENCES cajas(id),
        FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id)
    );
    ''')
    
    print("Insertando cajas por defecto...")
    cursor.execute('''
    INSERT OR IGNORE INTO cajas (id, nombre) VALUES 
    (1, 'Caja Diaria del Local'), 
    (2, 'Caja Banco Galicia'), 
    (3, 'Caja Cheques/Echeq'), 
    (4, 'Caja Principal'), 
    (5, 'Caja Retenciones');
    ''')
    
    conn.commit()
    conn.close()
    
    print("Migración de cajas completada con éxito.")

if __name__ == "__main__":
    migrate_cajas()
