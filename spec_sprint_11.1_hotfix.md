# Especificación: Sprint 11.1 Hotfix - Buscador en Móvil

## 1. Arreglar Input de Búsqueda de Productos
**Problema:** En pantallas móviles, el campo `#searchSaaS` (Buscar producto) se aplasta y queda inservible porque el botón "+ Concepto Libre" le roba el espacio en el contenedor `display: flex`. Además, ambos tienen `width: 100%` por el parche anterior, pero al estar en una fila (`row`) sin `flex-wrap`, chocan.
**Solución requerida:** 
- En `templates/cotizador.html`, agregar una clase `search-toolbar` al div que contiene el input y el botón de concepto libre: `<div class="search-toolbar" style="display: flex; gap: 10px;">`.
- En el bloque `<style>` del `@media (max-width: 768px)`, agregar las reglas para que la barra de búsqueda apile el input y el botón:
  ```css
  .search-toolbar { flex-direction: column !important; }
  #searchSaaS { padding: 12px !important; font-size: 16px !important; }
  ```
  Esto hará que el input sea más grande, legible y fácil de tocar con el dedo, y que el botón "+ Concepto Libre" pase a estar justo debajo ocupando todo el ancho sin aplastar al buscador.
