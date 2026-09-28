import sqlite3
import os
db_path = os.environ.get('DATA_DIR', './data') + '/disgraf_hub.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('ALTER TABLE pagos ADD COLUMN tipo_cheque TEXT DEFAULT "propio"')
cursor.execute('ALTER TABLE pagos ADD COLUMN librador_nombre TEXT')
cursor.execute('ALTER TABLE pagos ADD COLUMN librador_cuit TEXT')
conn.commit()
conn.close()
print("Migración completada.")
