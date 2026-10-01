import sqlite3
import os

db_path = os.environ.get('DATA_DIR', './data') + '/disgraf_hub.db'
if not os.path.exists(db_path):
    print("Database not found at", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    SELECT id, tipo_comprobante, subtotal, total_iva, total 
    FROM comprobantes 
    WHERE fecha_emision >= '2026-09-29' AND tipo_comprobante != 'Recibo de Pago'
''')
rows = cursor.fetchall()

print(f"Corrigiendo {len(rows)} comprobantes...")

for row in rows:
    c_id, tipo, subtotal, total_iva, total = row
    
    true_subtotal = round((subtotal or 0) / 1.21, 2)
    true_total_iva = round((total_iva or 0) / 1.21, 2)
    true_total = round((total or 0) / 1.21, 2)
    
    cursor.execute('''
        UPDATE comprobantes 
        SET subtotal = ?, total_iva = ?, total = ?
        WHERE id = ?
    ''', (true_subtotal, true_total_iva, true_total, c_id))
    
    cursor.execute('SELECT id, precio_unitario, subtotal FROM comprobantes_items WHERE comprobante_id = ?', (c_id,))
    items = cursor.fetchall()
    for it in items:
        it_id, it_precio, it_subtotal = it
        true_it_precio = round((it_precio or 0) / 1.21, 2)
        true_it_subtotal = round((it_subtotal or 0) / 1.21, 2)
        cursor.execute('''
            UPDATE comprobantes_items 
            SET precio_unitario = ?, subtotal = ?
            WHERE id = ?
        ''', (true_it_precio, true_it_subtotal, it_id))

cursor.execute('''
    SELECT id, monto, comprobante_id 
    FROM cajas_movimientos 
    WHERE comprobante_id IS NOT NULL AND DATE(fecha) >= '2026-09-29'
''')
movs = cursor.fetchall()
for m in movs:
    m_id, monto, c_id = m
    if c_id in [r[0] for r in rows]:
        true_monto = round((monto or 0) / 1.21, 2)
        cursor.execute('UPDATE cajas_movimientos SET monto = ? WHERE id = ?', (true_monto, m_id))

conn.commit()
conn.close()
print("¡Base de datos corregida con éxito!")
