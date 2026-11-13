# Tareas para Implementador ERP (Backend)

Hola Implementador ERP. Estamos en el Ciclo 25.
El usuario está intentando emitir una **Nota de Débito A** ante ARCA/AFIP y el sistema arrojó el siguiente error:
`Error en AFIP: Tipo de factura no reconocido: 'Nota de Débito A'`

**Causa raíz:**
En `afip_service.py`, el diccionario `tipo_map` no tiene configurados los códigos de comprobante de AFIP para las Notas de Débito (Código 2 para A y Código 7 para B). Además, en `routes/ventas_api.py`, al vincular un comprobante asociado (`cbte_asoc`), se asume que el padre siempre es una Factura (1 o 6), cuando en este caso el padre es una Nota de Crédito (código 3).

**Archivos a modificar:**
1. `afip_service.py`
2. `routes/ventas_api.py`

---

### 1. `afip_service.py`
1. En la función `emitir_factura` (alrededor de la línea 260), amplía el diccionario `tipo_map`:
```python
    tipo_map = {
        "Factura Electrónica A": 1,
        "Nota de Débito A": 2,
        "Nota de Crédito A": 3,
        "Factura Electrónica B": 6,
        "Nota de Débito B": 7,
        "Nota de Crédito B": 8,
    }
```
2. En la validación de CUIT (alrededor de la línea 282), asegúrate de que aplique a todos los comprobantes "A":
```python
    # Regla AFIP: Comprobantes A (1, 2, 3) solo pueden emitirse con CUIT válido (DocTipo=80)
    if tipo_cbte in (1, 2, 3) and (doc_tipo != 80 or doc_nro == 0):
        raise ValueError(
            "Los comprobantes 'A' (Factura, Nota de Débito y Nota de Crédito) requieren un cliente Responsable Inscripto con CUIT válido."
        )
```

---

### 2. `routes/ventas_api.py`
En la función `crear_comprobante` (alrededor de las líneas 103 a 114), dentro del bloque donde se construye `cbte_asoc`:
Actualmente el código dice:
`tipo_num = 1 if "A" in tipo_orig_str else 6`
Reemplázalo por un mapeo completo según el tipo real del comprobante padre:
```python
            cbte_asoc = None
            if ("Nota de Crédito" in comprobante.tipo_comprobante or "Nota de Débito" in comprobante.tipo_comprobante) and comprobante.comprobante_asociado_id:
                with sqlite3.connect(db_path) as conn_asoc:
                    row_asoc = conn_asoc.execute(
                        "SELECT numero_afip, tipo_comprobante FROM comprobantes WHERE id = ?",
                        (comprobante.comprobante_asociado_id,)
                    ).fetchone()
                    if row_asoc and row_asoc[0]:
                        nro_orig = int(row_asoc[0])
                        tipo_orig_str = row_asoc[1]
                        tipo_asoc_map = {
                            "Factura Electrónica A": 1,
                            "Nota de Débito A": 2,
                            "Nota de Crédito A": 3,
                            "Factura Electrónica B": 6,
                            "Nota de Débito B": 7,
                            "Nota de Crédito B": 8,
                        }
                        tipo_num = tipo_asoc_map.get(tipo_orig_str, 1 if "A" in tipo_orig_str else 6)
                        cbte_asoc = {'tipo': tipo_num, 'pto_vta': 10, 'nro': nro_orig, 'cuit': cuit_cliente}
```

**Regla estricta:** Solo implementa estos cambios en los archivos y avísame cuando esté listo para pasar al Verificador ERP. No ejecutes tests ni auditorías por tu cuenta.

