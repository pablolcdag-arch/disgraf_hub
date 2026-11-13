# Tareas para Implementador Front

Hola Implementador Front. Estamos en el Ciclo 24.
Tenemos dos correcciones fundamentales que resolver en el frontend:

**Archivos a modificar:**
1. `templates/clientes.html`
2. `templates/cotizador.html`

---

### 1. Corregir la Leyenda "Vinculado a..." en la Cuenta Corriente (`templates/clientes.html`)
**Problema:**
En `templates/clientes.html`, la tabla de comprobantes no muestra la leyenda "Vinculado a factura numero X" porque en la función que hace el fetch de comprobantes, se descartan los campos de vinculación.
**Solución:**
En `templates/clientes.html`, busca la función (aprox. línea 455):
```javascript
        // Fetch new DB history
        let dbHistory = [];
        try {
            const vRes = await fetch(`/api/ventas/cliente/${id}`);
            if (vRes.ok) {
                const dbData = await vRes.json();
                dbHistory = dbData.map(db => ({
                    id: db.id,
                    date: db.fecha_emision,
                    seller: "Sistema",
                    total: db.total,
                    products: [{}], // Mock for UI count
                    tipo_comprobante: db.tipo_comprobante,
                    impacta_cc: db.impacta_cc
                }));
            }
        } catch(e) { console.error(e); }
```
**Modificación:**
Agrega dentro del objeto retornado por el `.map` los campos `comprobante_asociado_id` y `asociado_tipo`:
```javascript
                dbHistory = dbData.map(db => ({
                    id: db.id,
                    date: db.fecha_emision,
                    seller: "Sistema",
                    total: db.total,
                    products: [{}], // Mock for UI count
                    tipo_comprobante: db.tipo_comprobante,
                    impacta_cc: db.impacta_cc,
                    comprobante_asociado_id: db.comprobante_asociado_id,
                    asociado_tipo: db.asociado_tipo
                }));
```
Con este cambio, `q.comprobante_asociado_id` existirá en el objeto y se renderizará automáticamente la leyenda debajo del tipo de comprobante.

---

### 2. Conservar Descuentos de Factura Original en `+ NC` (`templates/cotizador.html`)
**Problema:**
Cuando una factura original tiene descuentos en sus ítems (por ejemplo, 5% de descuento), al presionar `+ NC` el cotizador carga el precio de lista pero hardcodea `discount: 0`. Esto hace que la Nota de Crédito se genere por un importe mayor al de la factura original.
**Solución:**
En `templates/cotizador.html`, ubica el bloque `} else if (urlParams.get('nc_from')) {` (aprox. línea 1165).
Al mapear `comprobante.items` para poblar `state.cart`:
Calcula el descuento efectivo comparando el subtotal del ítem con el total nominal (`basePrice * item.cantidad`):
```javascript
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
```

**Regla estricta:** Solo implementa estos cambios en los archivos indicados y avísame cuando esté listo para pasar al Verificador Front. No ejecutes pruebas de consola ni verificación propia.

