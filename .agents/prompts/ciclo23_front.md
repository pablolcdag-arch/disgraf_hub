# Tareas para Implementador Front

Hola Implementador Front. Estamos en el Ciclo 23.
Tenemos dos problemas en el Front que están causando conflictos con la generación de Notas de Crédito y la visualización de comprobantes vinculados.

**Archivos a modificar:**
1. `templates/cotizador.html`
2. `templates/clientes.html`

### 1. Bug del Doble IVA en Notas de Crédito
El usuario reporta que al hacer clic en `+ NC` desde una Factura B, el sistema vuelve a calcular el IVA sobre los montos.
*Causa raíz:* En la base de datos, el `precio_unitario` de los ítems de las Facturas B y comprobantes internos se guarda con el IVA ya incluido (precio bruto). Cuando el Cotizador carga esos ítems al carrito (a través del bloque `nc_from`), asume que son precios netos y vuelve a multiplicar por 1.21 al renderizar el carrito para la Nota de Crédito B.
*Solución:*
En `templates/cotizador.html`, busca el bloque `} else if (urlParams.get('nc_from')) {`.
Dentro de ese bloque, al hacer el `.map()` sobre `comprobante.items` para llenar `state.cart`, debes revertir el IVA si el comprobante original era Tipo B o Interna, dividiendo el `precio_unitario` por 1.21.

Sustituye:
```javascript
                state.cart = comprobante.items.map(item => ({
                    product: {
                        id: item.producto_id,
                        name: item.descripcion,
                        price: item.precio_unitario,
                        unit: 'unid.'
                    },
```
Por algo como:
```javascript
                let isOriginalTipoB = tipoOriginal.includes('B') || tipoOriginal.includes('Interna');
                let ivaDivisor = isOriginalTipoB ? 1.21 : 1.0;
                
                state.cart = comprobante.items.map(item => ({
                    product: {
                        id: item.producto_id,
                        name: item.descripcion,
                        price: item.precio_unitario / ivaDivisor,
                        unit: 'unid.'
                    },
```

### 2. Bug de Sintaxis HTML en el Listado de Clientes
En `templates/clientes.html`, recientemente añadiste la leyenda de "Vinculado a...". Esto funciona, pero añadiste esa etiqueta HTML (`<br><span...>`) directamente a la variable `tipoComp`.
El problema es que `tipoComp` luego se inyecta como argumento dentro del atributo `onclick` del botón de descarga:
`onclick="downloadPDF('${q.id}', '${tipoComp}', '${q.date}')"`
Las comillas dobles que utilizaste dentro del `style="..."` de la etiqueta span rompen prematuramente el cierre del atributo `onclick=""`, lo que invalida el HTML y provoca que el botón no funcione o no envíe la información correcta al generador de PDF.

*Solución:*
En `templates/clientes.html` (alrededor de la línea 565, dentro de `renderClientHistory`), separa la variable limpia de la variable con HTML.
1. Crea `let tipoCompRaw = q.tipo_comprobante || 'Presupuesto A';`
2. `let tipoCompHTML = tipoCompRaw;`
3. Si hay `q.comprobante_asociado_id`, añádele el `<br><span>...` a `tipoCompHTML`.
4. Utiliza `tipoCompHTML` en el HTML de la celda de la tabla (`<td>`).
5. Utiliza rigurosamente `tipoCompRaw` en TODOS los `includes()` (ej. `if (tipoCompRaw.includes('Presupuesto'))`) y dentro de los atributos generados como `onclick="downloadPDF('${q.id}', '${tipoCompRaw}', '${q.date}')"` y en el enlace de `+ NC` para `tipo_original`.

**Regla estricta:** 
No realices pruebas propias escribiendo scripts de verificación. Simplemente implementa los cambios en los templates y avísame para que pase el testigo al Verificador.

