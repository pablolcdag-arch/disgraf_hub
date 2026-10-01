import re

# Fix double IVA in clientes.html reprintPDF
with open('templates/clientes.html', 'r') as f:
    content = f.read()

content = content.replace("total: dbComp.total,", "total: dbComp.subtotal || dbComp.total,")

with open('templates/clientes.html', 'w') as f:
    f.write(content)

# Fix CbteAsoc in afip_service.py
with open('afip_service.py', 'r') as f:
    afip_code = f.read()

if "cbte_asoc.get('cuit')" not in afip_code:
    afip_code = afip_code.replace(
        '''        cbte_asoc_xml = (
            "<ar:CbtesAsoc>"
            "<ar:CbteAsoc>"
            f"<ar:Tipo>{cbte_asoc['tipo']}</ar:Tipo>"
            f"<ar:PtoVta>{cbte_asoc['pto_vta']}</ar:PtoVta>"
            f"<ar:Nro>{cbte_asoc['nro']}</ar:Nro>"
            "</ar:CbteAsoc>"
            "</ar:CbtesAsoc>"
        )''',
        '''        cuit_xml = f"<ar:Cuit>{cbte_asoc['cuit']}</ar:Cuit>" if cbte_asoc.get('cuit') and cbte_asoc['cuit'] != "0" else ""
        cbte_asoc_xml = (
            "<ar:CbtesAsoc>"
            "<ar:CbteAsoc>"
            f"<ar:Tipo>{cbte_asoc['tipo']}</ar:Tipo>"
            f"<ar:PtoVta>{cbte_asoc['pto_vta']}</ar:PtoVta>"
            f"<ar:Nro>{cbte_asoc['nro']}</ar:Nro>"
            f"{cuit_xml}"
            "</ar:CbteAsoc>"
            "</ar:CbtesAsoc>"
        )'''
    )

with open('afip_service.py', 'w') as f:
    f.write(afip_code)

# Fix ventas_api.py
with open('routes/ventas_api.py', 'r') as f:
    ventas_code = f.read()

if "'cuit': cuit_cliente" not in ventas_code:
    ventas_code = ventas_code.replace(
        "cbte_asoc = {'tipo': tipo_num, 'pto_vta': 10, 'nro': nro_orig}",
        "cbte_asoc = {'tipo': tipo_num, 'pto_vta': 10, 'nro': nro_orig, 'cuit': cuit_cliente}"
    )

with open('routes/ventas_api.py', 'w') as f:
    f.write(ventas_code)

print("Fixes applied successfully")
