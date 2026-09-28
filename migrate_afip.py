import sqlite3
import os

# Ajusta el DATA_DIR según tu estructura, normalmente es './data'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE comprobantes ADD COLUMN cae TEXT")
except sqlite3.OperationalError:
    print("cae ya existe")

try:
    cursor.execute("ALTER TABLE comprobantes ADD COLUMN cae_vto TEXT")
except sqlite3.OperationalError:
    print("cae_vto ya existe")

try:
    cursor.execute("ALTER TABLE comprobantes ADD COLUMN numero_afip INTEGER")
except sqlite3.OperationalError:
    print("numero_afip ya existe")

conn.commit()
conn.close()
print("Migración de Base de Datos para AFIP completada.")
