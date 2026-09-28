import sqlite3
import os

def migrate():
    data_dir = os.environ.get('DATA_DIR', './data')
    db_path = os.path.join(data_dir, 'disgraf_hub.db')
    
    print(f"Conectando a base de datos en: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener columnas existentes
    cursor.execute("PRAGMA table_info(clientes)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    required_columns = [
        ("categoria", "TEXT"),
        ("estado", "TEXT"),
        ("contacto", "TEXT"),
        ("telefonos", "TEXT"),
        ("domicilio", "TEXT"),
        ("localidad", "TEXT"),
        ("provincia", "TEXT"),
        ("mail", "TEXT"),
        ("condicion_iva", "TEXT"),
        ("razon_social", "TEXT"),
        ("cuit", "TEXT"),
        ("documento", "TEXT"),
        ("otro_tipo_documento", "TEXT"),
        ("moneda", "TEXT DEFAULT 'Pesos'"),
        ("observaciones", "TEXT"),
        ("observaciones_internas", "TEXT"),
        ("recordatorio", "TEXT"),
        ("codigo_postal", "TEXT"),
        ("lista_de_precio", "TEXT DEFAULT 'Lista 1'"),
        ("permite_cuenta_corriente", "BOOLEAN DEFAULT 0"),
        ("limite_cuenta_corriente", "REAL DEFAULT 0.0")
    ]
    
    added_count = 0
    
    for col_name, col_type in required_columns:
        if col_name not in existing_columns:
            print(f"Agregando columna faltante: {col_name} {col_type}")
            try:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_name} {col_type}")
                added_count += 1
            except Exception as e:
                print(f"Error al agregar columna {col_name}: {e}")
                
    conn.commit()
    conn.close()
    
    print(f"Migración completada. {added_count} columnas agregadas.")

if __name__ == "__main__":
    migrate()

