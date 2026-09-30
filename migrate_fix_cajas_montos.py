import sqlite3
import os

db_path = os.environ.get('DATA_DIR', './data') + '/disgraf_hub.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fix 1: Normalizar tipo a minúscula (Ingreso → ingreso, Egreso → egreso)
cursor.execute("SELECT COUNT(*) FROM cajas_movimientos WHERE tipo != LOWER(tipo)")
count = cursor.fetchone()[0]
print(f"Registros con tipo mal escrito (mayúscula): {count}")

cursor.execute("UPDATE cajas_movimientos SET tipo = LOWER(tipo) WHERE tipo != LOWER(tipo)")
conn.commit()
print(f"Registros normalizados: {cursor.rowcount}")

# Fix 2: Por si hay montos negativos en tipo=ingreso
cursor.execute("SELECT COUNT(*) FROM cajas_movimientos WHERE tipo = 'ingreso' AND monto < 0")
count2 = cursor.fetchone()[0]
print(f"Registros ingreso con monto negativo: {count2}")

if count2 > 0:
    cursor.execute("UPDATE cajas_movimientos SET monto = ABS(monto) WHERE tipo = 'ingreso' AND monto < 0")
    conn.commit()
    print(f"Montos negativos corregidos: {cursor.rowcount}")

conn.close()
print("Migración completada.")
