# Tareas para Implementador Front

Hola Implementador Front. Estamos en el Ciclo 25.
El usuario necesita emitir una **Nota de Débito** para anular/compensar una Nota de Crédito errónea, y necesitamos habilitar el flujo completo tanto manual como automático.

**Archivos a modificar:**
1. `templates/clientes.html`
2. `templates/cotizador.html`

---

### 1. `templates/clientes.html` (Botón + ND en Notas de Crédito)
En `renderClientHistory` (alrededor de la línea 580):
Agrega la opción para que las filas de `Nota de Crédito` muestren el botón `+ ND`:
```javascript
                        if (tipoCompRaw.includes('Presupuesto')) {
                            actions += `<a href="/cotizador?load_id=${q.id}" class="btn-secondary" style="font-size: 11px; padding: 4px 8px; text-decoration: none; color: white;" title="Facturar">$ / Facturar</a>`;
                        } else if (tipoCompRaw.includes('Factura')) {
                            actions += `
                                <button onclick="openPaymentModal('${q.id}')" class="btn-primary" style="font-size: 11px; padding: 4px 8px; background: #10b981;">Cobrar</button>
                                <a href="/cotizador?remito_from=${q.id}" class="btn-secondary" style="font-size: 11px; padding: 4px 8px; text-decoration: none; color: white;">+ Remito</a>
                                <a href="/cotizador?nc_from=${q.id}&tipo_original=${encodeURIComponent(tipoCompRaw)}" class="btn-secondary" style="font-size: 11px; padding: 4px 8px; text-decoration: none; color: white; border-color: rgba(239, 68, 68, 0.3);">+ NC</a>
                            `;
                        } else if (tipoCompRaw.includes('Nota de Crédito')) {
                            actions += `
                                <a href="/cotizador?nd_from=${q.id}&tipo_original=${encodeURIComponent(tipoCompRaw)}" class="btn-secondary" style="font-size: 11px; padding: 4px 8px; text-decoration: none; color: white; border-color: rgba(239, 68, 68, 0.3);">+ ND</a>
                            `;
                        }
```

---

### 2. `templates/cotizador.html` (Soporte de URL param `nd_from`)
Ubica el bloque `} else if (urlParams.get('nc_from')) {` (aprox. línea 1170).
Añade a continuación un bloque `} else if (urlParams.get('nd_from')) {` similar al de `nc_from`, pero seleccionando `Nota de Débito A` (si `tipoOriginal.includes('A')`) o `Nota de Débito B`:
```javascript
    } else if (urlParams.get('nd_from')) {
        const ndFrom = urlParams.get('nd_from');
        const tipoOriginal = urlParams.get('tipo_original') || '';
        try {
            const res = await fetch(`/api/ventas/comprobante/${ndFrom}`);
            if (res.ok) {
                const comprobante = await res.json();
                
                const resCliente = await fetch('/api/clientes/' + comprobante.cliente_id);
                if (resCliente.ok) {
                    window.selectClient(await resCliente.json());
                } else {
                    window.selectedClientId = comprobante.cliente_id;
                    dom.clientName.value = comprobante.cliente_nombre || comprobante.cliente_id || "";
                }
                window.comprobanteAsociadoId = ndFrom;
                
                let isOriginalTipoB = tipoOriginal.includes('B') || tipoOriginal.includes('Interna');
                let ivaDivisor = isOriginalTipoB ? 1.21 : 1.0;
                
                state.cart = comprobante.items.map(item => {
                    let basePrice = (item.precio_unitario || 0) / ivaDivisor;
                    let lineSubtotal = (item.subtotal || 0) / ivaDivisor;
                    let nominalTotal = basePrice * item.cantidad;
                    let disc = 0;
                    if (nominalTotal > 0 && lineSubtotal < nominalTotal) {
                        disc = Math.round((1 - (lineSubtotal / nominalTotal)) * 10000) / 100;
                    }
                    return {
                        product: {
                            id: item.producto_id,
                            name: item.descripcion,
                            price: basePrice,
                            unit: 'unid.'
                        },
                        quantity: item.cantidad,
                        discount: disc
                    };
                });
                
                const tComp = document.getElementById('tipoComprobante');
                if (tComp) {
                    if (tipoOriginal.includes('A')) {
                        tComp.value = 'Nota de Débito A';
                    } else {
                        tComp.value = 'Nota de Débito B';
                    }
                }
                
                if (window.handleComprobanteChange) {
                    window.handleComprobanteChange();
                } else {
                    renderCart();
                }
            }
        } catch (e) {
            console.error("Error loading nd from url param", e);
        }
    }
```

**Regla estricta:** Solo implementa estos cambios en los archivos y avísame cuando esté listo para pasar al Verificador Front. No ejecutes tests ni verificación por tu cuenta.

