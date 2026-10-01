import sqlite3

conn = sqlite3.connect('data/disgraf_hub.db')
c = conn.cursor()
c.execute("SELECT id, tipo_comprobante, numero_afip FROM comprobantes")
print("comprobantes:", c.fetchall())
conn.close()
