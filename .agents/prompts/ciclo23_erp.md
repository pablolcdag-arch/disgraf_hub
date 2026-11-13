# Tareas para Implementador ERP (Backend)

Hola Implementador ERP. Estamos en el Ciclo 23.
Tenemos dos ajustes que hacer en la API del cotizador para asegurar la consistencia contable y visual de los PDF generados para Recibos de Pago y Notas de Crédito.

**Archivos a modificar:**
1. `routes/cotizador_api.py`

### 1. Agregar Leyenda de Vinculación en el PDF
Actualmente, los comprobantes vinculados (como un Recibo de un pago de Factura, o una Nota de Crédito asociada a una Factura) guardan el `comprobante_asociado_id` en la BD, pero el PDF generado no muestra ninguna referencia a ello.
El usuario solicitó: *"el recibo deberia tener la leyenda del comprobante al que hace referencia o sea el pago... deberia decir Recibo de pago Vinculado a factura numero X y asi deberia ser siempre que se vincula un comprobante"*.

**Modificaciones a realizar:**
En `routes/cotizador_api.py`, dentro de la función `api_generate_quote_pdf`:
1. Ubica el bloque donde se define el `right_cell_text` (alrededor de la línea 390-400), después de determinar `title_text`, `pto_vta`, `numero_afip` y `date_str`.
2. Añade lógica para consultar en la base de datos (haciendo JOIN a la misma tabla `comprobantes`) el tipo de comprobante padre en caso de que el `quote_id` posea un `comprobante_asociado_id`.
3. Si existe, extrae la primera palabra del tipo padre (ej. de "Factura Electrónica B" extraer "factura") en minúsculas.
4. Concatena a `right_cell_text` una nueva línea con fuente un poco más pequeña y en gris, similar a esto: `<br/><font size=10 color='#475569'>Vinculado a {tipo_padre} numero {padre_id}</font>`.

*Nota sobre la consulta BD:*
Asegúrate de envolver la consulta en un bloque `try/except: pass` para no romper la generación del PDF en caso de error. Puedes usar algo así:
```python
    asociado_leyenda = ""
    if quote_id:
        try:
            db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
            with sqlite3.connect(db_path) as conn:
                row_asoc = conn.execute('''
                    SELECT c2.id, c2.tipo_comprobante 
                    FROM comprobantes c1 
                    JOIN comprobantes c2 ON c1.comprobante_asociado_id = c2.id 
                    WHERE c1.id = ?
                ''', (quote_id,)).fetchone()
                if row_asoc:
                    parent_id, parent_type = row_asoc
                    parent_type_short = parent_type.split(' ')[0].lower()
                    asociado_leyenda = f"<br/><font size=10 color='#475569'>Vinculado a {parent_type_short} numero {parent_id}</font>"
        except Exception as e:
            print("Error buscando comprobante asociado:", e)
```
Y luego:
```python
    right_cell_text = f"<b>{title_text}</b><br/>"
    if numero_afip:
        right_cell_text += f"Nº {int(pto_vta):05d}-{int(numero_afip):08d}<br/>"
    right_cell_text += f"<b>Fecha:</b> {date_str}"
    if asociado_leyenda:
        right_cell_text += asociado_leyenda
```

**Regla estricta:** 
No realices pruebas propias escribiendo funciones de verificación. Simplemente implementa los cambios solicitados y avísame para que pase el testigo al Verificador.

