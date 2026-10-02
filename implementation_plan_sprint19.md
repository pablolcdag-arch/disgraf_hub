# Implementation Plan - Sprint 19: Categorías y Sitemap SSG

## Objetivos
Implementar la asignación de categorías para los artículos del blog satélite (`oficiocarteleria.com.ar`) y la generación automática de un `sitemap.xml` válido para mejorar el posicionamiento SEO.

## Arquitectura y Decisiones Técnicas
- **Almacenamiento:** Se agregará el campo `category` (string) al esquema de los posts en `data/marketing_content.json`. Si no tiene, por defecto será "Sin Categoría".
- **SSG (Static Site Generation):** 
  - La función `rebuild_static_site()` en `seo_service.py` extraerá las categorías únicas de los posts publicados.
  - Generará una página por cada categoría bajo el subdirectorio `categoria/{slug_categoria}.html`, reciclando la plantilla del index o utilizando una nueva.
  - Inyectará la lista de `categories` en el contexto Jinja de **todas** las páginas estáticas generadas, para que el menú de navegación (`oficio_base.html`) pueda iterar sobre ellas y construir los enlaces dinámicamente.
- **Sitemap XML:** Se generará un archivo `sitemap.xml` crudo en `BLOG_OUTPUT_DIR` incluyendo: la home (`/`), los posts (`/{slug}.html`), las páginas de categorías (`/categoria/{slug}.html`) y las páginas estáticas (`/about.html`, `/contacto.html`, `/legales.html`). 
- **Restricciones:** 
  - **PROHIBIDO** realizar imports dentro de las funciones (cumplimiento estricto de AGENTS.md).
  - Las URLs en el sitemap deben usar el dominio base `https://oficiocarteleria.com.ar`.

## Tareas para el Implementador ERP (Backend)
1. **`routes/marketing_api.py`:** Modificar los endpoints de creación/actualización de posts para aceptar y guardar el campo `category` en `marketing_content.json`.
2. **`seo_service.py`:** 
   - Modificar `rebuild_static_site()` para recolectar las categorías únicas.
   - Pasar la lista de categorías (`categories`) al renderizar `oficio_index.html`, `oficio_post.html` y las páginas estáticas.
   - Añadir la lógica para generar páginas de categoría usando Jinja (crear subcarpeta `categoria/` en `BLOG_OUTPUT_DIR` si es necesario y guardar los htmls ahí).
   - Añadir lógica de generación de `sitemap.xml` usando un template de string o Jinja e incluir todas las URLs válidas.

## Tareas para el Implementador Front (Frontend)
1. **`templates/marketing.html`:** Añadir un campo (input/select) para asignar "Categoría" en el modal/formulario de creación y edición del dashboard de marketing. Modificar el JavaScript para enviar este dato al backend.
2. **`templates/oficio_base.html`:** Modificar el menú de navegación (navbar) para iterar sobre la variable `categories` y generar enlaces tipo `<a href="/categoria/{{ cat.slug }}.html">{{ cat.name }}</a>`.
3. **Template de Categoría (opcional/reutilizar):** Asegurar que la vista de categorías se renderice correctamente (se puede reutilizar `oficio_index.html` modificando el título/contexto si es necesario).

## Flujo de Trabajo
1. El usuario delegará las tareas de Backend al Implementador ERP proporcionando el prompt exacto.
2. El usuario delegará las tareas de Frontend al Implementador Front proporcionando el prompt exacto.
3. El usuario pasará los resultados al Verificador.
4. El Coordinador ejecutará el deploy a producción.
