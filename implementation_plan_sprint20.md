# Implementation Plan - Sprint 20: Refactor UI de Categorías (Optimización SEO y UX)

## Objetivos
Mejorar la experiencia de usuario (UX) y el rastreo de motores de búsqueda (SEO) separando las categorías dinámicas del menú institucional principal, utilizando una barra de navegación secundaria (sub-header) deslizable.

## Arquitectura y Decisiones Técnicas
- **Enfoque SEO:** Se elige una "Barra Secundaria" (estilo *Pills* o *Topics* como en Medium) por sobre un menú desplegable oculto. Esto garantiza que:
  1. Los enlaces de categorías estén siempre visibles y a 1 clic de distancia.
  2. Los bots de Google los rastreen como enlaces prioritarios del DOM sin scripts ni CSS hiding.
  3. La experiencia en dispositivos móviles (celulares) sea óptima, permitiendo un *scroll horizontal* táctil sin lidiar con los problemas de "hover" de los dropdowns en pantallas táctiles.
- **Implementación:** Modificar exclusivamente `templates/oficio_base.html`.
- **Restricciones:** 
  - Solo CSS puro. Prohibido Javascript.
  - Asegurar responsividad (usar `overflow-x: auto` y `white-space: nowrap` para la barra secundaria).

## Tareas para el Implementador Front (Frontend)
1. **`templates/oficio_base.html`:** 
   - Limpiar el menú institucional principal (`<nav class="nav-menu">`) para que solo contenga: "Inicio", "Sobre Nosotros" y "Contacto".
   - Crear un nuevo contenedor `<div class="categories-bar">` justo debajo del `<header>` (o en el borde inferior del mismo).
   - Mover el bucle `{% for cat in categories %}` a esta nueva barra secundaria.
   - Agregar el CSS necesario en el bloque `<style>` de la cabecera para darle un diseño sutil a la barra (ej: fondo gris muy claro `#f3f4f6`, enlaces centrados, scroll horizontal en móviles, y sin barra de scroll visible `::-webkit-scrollbar { display: none; }`).
