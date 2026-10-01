import sys

# FIX BACKEND
file_path = "routes/ventas_api.py"
with open(file_path, "r") as f:
    content = f.read()

old_sql = """                        WHEN tipo_comprobante = 'Ajuste de Saldo' THEN -total
                        ELSE 0
                    END
                ) as saldo
            FROM comprobantes
            WHERE impacta_cc = 1
            GROUP BY cliente_id
            HAVING saldo > 1
            ORDER BY saldo DESC"""

new_sql = """                        WHEN tipo_comprobante = 'Ajuste de Saldo' THEN total
                        ELSE 0
                    END
                ) as saldo
            FROM comprobantes
            WHERE impacta_cc = 1
            GROUP BY cliente_id
            HAVING ABS(saldo) > 0.01
            ORDER BY saldo DESC"""

if old_sql in content:
    content = content.replace(old_sql, new_sql)
    with open(file_path, "w") as f:
        f.write(content)
    print("Fixed Backend SQL")
else:
    print("Could not find backend block")


# FIX FRONTEND
file_path_ui = "templates/clientes.html"
with open(file_path_ui, "r") as f:
    content_ui = f.read()

old_ui = """                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 12px 10px; color: var(--text-muted);">#${d.cliente_id}</td>
                    <td style="padding: 12px 10px; font-weight: bold; color: var(--text-main);">${clientName}</td>
                    <td style="padding: 12px 10px; text-align: right; color: #ef4444; font-weight: bold;">
                        ${formatter.format(d.saldo)}
                    </td>
                </tr>"""

new_ui = """                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 12px 10px; color: var(--text-muted);">#${d.cliente_id}</td>
                    <td style="padding: 12px 10px; font-weight: bold; color: var(--text-main);">${clientName}</td>
                    <td style="padding: 12px 10px; text-align: right; color: ${d.saldo > 0 ? '#ef4444' : '#10b981'}; font-weight: bold;">
                        ${formatter.format(d.saldo)}
                    </td>
                </tr>"""

if old_ui in content_ui:
    content_ui = content_ui.replace(old_ui, new_ui)
else:
    print("Could not find frontend block 1")

old_header = """                        <th style="padding: 10px; text-align: right;">Saldo Deudor</th>"""
new_header = """                        <th style="padding: 10px; text-align: right;">Saldo Actual</th>"""
if old_header in content_ui:
    content_ui = content_ui.replace(old_header, new_header)

old_empty = """tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px; color: var(--text-muted);">No hay clientes con saldo deudor.</td></tr>';"""
new_empty = """tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px; color: var(--text-muted);">No hay clientes con saldos pendientes.</td></tr>';"""
if old_empty in content_ui:
    content_ui = content_ui.replace(old_empty, new_empty)

with open(file_path_ui, "w") as f:
    f.write(content_ui)
print("Fixed Frontend")

