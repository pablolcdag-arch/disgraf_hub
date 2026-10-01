import sys

file_path = "routes/clientes_api.py"
with open(file_path, "r") as f:
    content = f.read()

old_block = """            if "Factura" in tipo or "Nota de Débito" in tipo or "Presupuesto" in tipo:
                debe = total
                saldo += total
            elif "Recibo" in tipo or "Nota de Crédito" in tipo:
                haber = total
                saldo -= total"""

new_block = """            if "Factura" in tipo or "Nota de Débito" in tipo or "Presupuesto" in tipo:
                debe = total
                saldo += total
            elif "Recibo" in tipo or "Nota de Crédito" in tipo:
                haber = total
                saldo -= total
            elif "Ajuste de Saldo" in tipo:
                if total >= 0:
                    debe = total
                else:
                    haber = abs(total)
                saldo += total"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w") as f:
        f.write(content)
    print("Fix PDF applied.")
else:
    print("Could not find block in routes/clientes_api.py")
