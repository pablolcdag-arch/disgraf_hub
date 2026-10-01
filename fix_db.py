import sqlite3

conn = sqlite3.connect('data/disgraf_hub.db')
c = conn.cursor()
c.execute("SELECT id, tipo_comprobante, subtotal, total_iva, total, fecha_emision FROM comprobantes")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()
