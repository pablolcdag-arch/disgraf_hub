# Especificación: Sprint 11 - Pre-Lanzamiento (Exportación, Manual y Responsive)

## 1. Exportar Clientes a CSV
**Problema:** Los usuarios no pueden extraer la base de datos de clientes desde la interfaz.
**Solución requerida:** 
- **Backend:** Endpoint `GET /api/clientes/export` que consulte `SELECT * FROM clientes`, convierta los registros a un string CSV usando el módulo `csv` e `io.StringIO`, y devuelva un `StreamingResponse` o `Response` con `media_type="text/csv"` y `Content-Disposition` para descargarlo como `clientes_disgraf.csv`.
- **Frontend:** En `templates/clientes.html`, agregar un botón `⬇️ Exportar CSV` que sea un `<a href="/api/clientes/export">` al lado del botón "+ Nuevo Cliente".

## 2. Responsividad Móvil (Especialmente Cotizador)
**Problema:** La vista del Cotizador Rápido se rompe en pantallas pequeñas porque usa un flex layout forzado en fila.
**Solución requerida:** 
- Identificar los contenedores con `display: flex` estático (como el `2 Pane Layout` del cotizador).
- Asignarles clases semánticas (ej: `split-layout`, `toolbar-actions`) o inyectar un bloque `<style>` con `@media (max-width: 768px)` que cambie el `flex-direction` a `column`, quite restricciones estrictas de `max-height: calc(...)` y haga que los paneles fluyan naturalmente hacia abajo.
- Asegurar que la barra de navegación superior no desborde en móvil.

## 3. Manual de Usuario PDF / HTML
**Problema:** Los vendedores necesitan una referencia de uso del sistema.
**Solución requerida:**
- Crear un nuevo template estático `templates/manual.html` que contenga un documento bien maquetado (Tipografía clara, secciones, índice) explicando: 
  1) Diferencia entre Cotizador y Facturación.
  2) Cómo buscar productos.
  3) Notas de Crédito y Remitos.
  4) Gestión de Cuenta Corriente.
- En `routes/ui.py` (o donde se sirvan las vistas), agregar un endpoint `@router.get("/manual")` que renderice ese template.
- Agregar un botón "🖨️ Imprimir / Guardar PDF" que ejecute `window.print()` en el navegador con estilos `@media print` optimizados.
