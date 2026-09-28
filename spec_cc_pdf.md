# Especificación: Fix de Datos de Cliente y Descarga de Cuenta Corriente

## 1. Fix: Datos de Cliente en Cotizador (Nota de Crédito)
**Problema:** Al hacer clic en "+ NC" desde el historial de un cliente, la página del Cotizador carga la factura original y asocia el ID del cliente (`659`), pero NO descarga sus datos fiscales (CUIT, Domicilio, Condición de IVA) ni su nombre real. Por ende, cuando se emite la NC, el PDF generado dice "Cliente: 659" sin los detalles fiscales obligatorios.
**Solución requerida:** En `templates/cotizador.html`, al procesar los parámetros de URL (`nc_from` o `remito_from`), después de hacer el fetch de `/api/ventas/comprobante/{id}`, se debe hacer un fetch adicional a `/api/clientes/{cliente_id}`. Con el JSON resultante, se debe llamar a la función `selectClient(client)` (que ya existe) para que popule correctamente el formulario y el objeto `window.selectedClientData`.

## 2. Nueva Feature: Descarga de Cuenta Corriente (PDF)
**Problema:** No existe forma de entregarle al cliente un resumen de sus movimientos.
**Solución requerida:** 
- **Backend (`routes/clientes_api.py`):** Crear un endpoint `GET /api/clientes/{id}/cuenta_corriente/pdf`.
  - Debe buscar los datos del cliente.
  - Debe buscar el historial de comprobantes en `comprobantes` (donde `cliente_id = ? AND impacta_cc = 1`) ordenados por `fecha_emision ASC`.
  - Debe iterar sobre los comprobantes para calcular el saldo acumulado (las Facturas y Notas de Débito SUMAN al saldo que nos deben; los Recibos de Pago y Notas de Crédito RESTAN al saldo).
  - Usar `reportlab` para generar un PDF en A4 con el logo o título de Disgraf, los datos del cliente, y una tabla con: `Fecha | Comprobante | Debe | Haber | Saldo`.
  - Retornar el PDF como un `StreamingResponse` (o FileResponse) con mimetype `application/pdf` y cabecera de descarga (attachment).
- **Frontend (`templates/clientes.html`):** En la cabecera de la ficha del cliente, añadir un botón "📄 Descargar CC (PDF)" que abra la URL de este endpoint en una nueva pestaña o fuerce la descarga.
