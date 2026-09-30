import sqlite3
import os

db_path = os.environ.get('DATA_DIR', './data') + '/disgraf_hub.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM cajas_movimientos WHERE tipo = 'Ingreso' AND monto < 0")
count = cursor.fetchone()[0]
print(f"Registros a corregir: {count}")

cursor.execute("UPDATE cajas_movimientos SET monto = ABS(monto) WHERE tipo = 'Ingreso' AND monto < 0")
conn.commit()
print(f"Registros corregidos: {cursor.rowcount}")
conn.close()
print("Migración completada.")

