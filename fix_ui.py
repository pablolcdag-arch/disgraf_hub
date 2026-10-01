import sys
import re

file_path = "templates/clientes.html"
with open(file_path, "r") as f:
    content = f.read()

old_block = """    // Filter history based on tab
    let filteredHistory = history;
    if (tab === 'todos') {
        filteredHistory = history.filter(q => q.impacta_cc === 1);
    } else if (tab === 'presupuestos') {"""

new_block = """    // Filter history based on tab
    let filteredHistory = history;
    if (tab === 'todos') {
        filteredHistory = history.filter(q => q.impacta_cc === 1);
        
        // Calculate running balance (saldo)
        filteredHistory.sort((a,b) => new Date(a.date) - new Date(b.date) || a.id - b.id);
        let saldo = 0;
        filteredHistory.forEach(q => {
            const tipo = q.tipo_comprobante || '';
            const total = q.total || 0;
            if (tipo.includes('Factura') || tipo.includes('Nota de Débito') || tipo.includes('Presupuesto')) {
                saldo += total;
                q.debe = total;
                q.haber = 0;
            } else if (tipo.includes('Recibo') || tipo.includes('Nota de Crédito')) {
                saldo -= total;
                q.debe = 0;
                q.haber = total;
            } else if (tipo.includes('Ajuste de Saldo')) {
                if (total >= 0) {
                    q.debe = total;
                    q.haber = 0;
                } else {
                    q.debe = 0;
                    q.haber = Math.abs(total);
                }
                saldo += total;
            }
            q.saldo = saldo;
        });
        filteredHistory.sort((a,b) => new Date(b.date) - new Date(a.date) || b.id - a.id);
        
    } else if (tab === 'presupuestos') {"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Injected balance calc")
else:
    print("Could not find block 1")


old_th_block = """                        <th style="padding: 10px;">Fecha</th>
                        <th style="padding: 10px;">Tipo</th>
                        <th style="padding: 10px;">Número</th>
                        <th style="padding: 10px; text-align: right;">Importe</th>
                        <th style="padding: 10px; text-align: center;">Acciones</th>"""

new_th_block = """                        <th style="padding: 10px;">Fecha</th>
                        <th style="padding: 10px;">Tipo</th>
                        <th style="padding: 10px;">Número</th>
                        ${tab === 'todos' ? `
                        <th style="padding: 10px; text-align: right;">Deuda</th>
                        <th style="padding: 10px; text-align: right;">Pago</th>
                        <th style="padding: 10px; text-align: right;">Saldo</th>
                        ` : `
                        <th style="padding: 10px; text-align: right;">Importe</th>
                        `}
                        <th style="padding: 10px; text-align: center;">Acciones</th>"""

if old_th_block in content:
    content = content.replace(old_th_block, new_th_block)
    print("Injected th")
else:
    print("Could not find th block")

old_td_block = """                            <td style="padding: 12px 10px; font-size: 13px; color: var(--text-muted);">${q.id}</td>
                            <td style="padding: 12px 10px; font-size: 13px; text-align: right; font-weight: bold;">$${q.total.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
                            <td style="padding: 12px 10px; text-align: center; display: flex; justify-content: center; gap: 5px;">"""

new_td_block = """                            <td style="padding: 12px 10px; font-size: 13px; color: var(--text-muted);">${q.id}</td>
                            ${tab === 'todos' ? `
                            <td style="padding: 12px 10px; font-size: 13px; text-align: right; color: #ef4444;">${q.debe ? '$' + q.debe.toLocaleString('es-AR', {minimumFractionDigits: 2}) : ''}</td>
                            <td style="padding: 12px 10px; font-size: 13px; text-align: right; color: #10b981;">${q.haber ? '$' + q.haber.toLocaleString('es-AR', {minimumFractionDigits: 2}) : ''}</td>
                            <td style="padding: 12px 10px; font-size: 13px; text-align: right; font-weight: bold; color: #38bdf8;">$${q.saldo.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
                            ` : `
                            <td style="padding: 12px 10px; font-size: 13px; text-align: right; font-weight: bold;">$${q.total.toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
                            `}
                            <td style="padding: 12px 10px; text-align: center; display: flex; justify-content: center; gap: 5px;">"""

if old_td_block in content:
    content = content.replace(old_td_block, new_td_block)
    print("Injected td")
else:
    print("Could not find td block")

with open(file_path, "w") as f:
    f.write(content)
