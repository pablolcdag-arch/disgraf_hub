import re

with open('routes/catalog_api.py', 'r') as f:
    content = f.read()

bad_query = '''cursor.execute("SELECT codigo, nombre, rubro, precio_final, unidad, iva_porcentaje FROM productos WHERE habilitado = 1")
        rows = cursor.fetchall()
        for row in rows:
            p_id, p_name, p_cat, p_price_final, p_unit, p_iva = row
            p_iva = float(p_iva) if p_iva else 21.0
            
            # EL FRONTEND ESPERA EL PRECIO NETO (SIN IVA)
            # Porque luego el frontend le suma el IVA segun sea Factura A o Factura B.
            p_price = p_price_final / (1 + p_iva / 100) if p_price_final else 0.0
            
            # Format price back to string as expected by frontend
            p_price_str = f"{p_price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if p_price else "0,00"'''

good_query = '''cursor.execute("SELECT codigo, nombre, rubro, precio_final, unidad FROM productos WHERE habilitado = 1")
        rows = cursor.fetchall()
        for row in rows:
            p_id, p_name, p_cat, p_price, p_unit = row
            # Format price back to string as expected by frontend
            # The previous frontend expects something like "1.234,56" or just string
            p_price_str = f"{p_price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if p_price else "0,00"'''

content = content.replace(bad_query, good_query)

with open('routes/catalog_api.py', 'w') as f:
    f.write(content)

print("Catalog API reverted")
