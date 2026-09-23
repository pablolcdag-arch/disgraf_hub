# Bitácora de Decisiones (Decisions Log) - Disgraf Hub

Este documento rastrea las decisiones estratégicas y arquitectónicas clave tomadas durante el desarrollo de Disgraf Hub. La Inteligencia Artificial debe leer este documento para entender el **"por qué"** detrás de las directivas actuales y evitar cuestionar o proponer alternativas que ya fueron descartadas (prevención de "loops").

---

## [21 de Septiembre 2026] - Migración SDK IA: google-generativeai → google-genai (SDD Ciclo 2)
- **Decisión:** Migrar de `google-generativeai` (deprecado) a `google-genai` como SDK oficial de Google Gemini.
- **Razón:** El paquete `google.generativeai` fue declarado oficialmente deprecado. El nuevo `google-genai` (v2.24.0) ofrece API unificada con `genai.Client`, mejor soporte async vía `client.aio`, y es el camino oficial de Google hacia adelante.
- **Cambios aplicados:**
  - `requirements.txt`: `google-generativeai` → `google-genai`
  - `seo_service.py`, `seo_agent.py`, `main.py`, `test_gemini.py`: `from google import genai`, cliente global `gemini_client = genai.Client(api_key=...)`, llamadas `client.models.generate_content(model=..., contents=...)`
  - Eliminados imports de genai dentro de funciones en `main.py` L1129 y L1741 (doble corrección de antipatrón AGENTS.md §8)
- **Patrón canónico:** cliente global a nivel módulo; modelo como string en cada llamada.
- **Verificación:** `test_gemini.py` con `gemini-3.6-flash` → `Success ✅`

---

## [05 de Septiembre 2026] - Estrategia SEO y Dominio del Blog
- **Decisión:** El blog generado por IA **NO** debe alojarse en `disgraf.com.ar/blog`.
- **Razón:** El objetivo es mejorar el SEO Off-page. Al alojar los artículos en un dominio independiente (`oficiocarteleria.com.ar`), simulamos que un tercero (una revista o blog de la industria gráfica) está recomendando a Disgraf Insumos Gráficos hacia el final de sus notas. Esto genera *backlinks* externos valiosos que incrementan la autoridad del dominio principal en Google.

---

## [05 de Septiembre 2026] - Reestructuración V2 vs WooCommerce
- **Decisión:** El objetivo central del proyecto es desarrollar una **V2 (Versión 2)** completa de la página web desde cero, y no limitarse a sincronizar datos con una instalación vieja de WordPress/WooCommerce.
- **Razón:** Disgraf Hub debe evolucionar hacia un ERP/CRM completo (reemplazando a SAAS Argentina). Intentar atar esta inmensa lógica (cotizador físico, integración ARCA, cuentas corrientes de clientes) a una arquitectura vieja de WooCommerce limitaba el desarrollo y ensuciaba el código. El botón "Sincronizar Web" del dashboard actual alimenta la nueva V2, y se prohíbe retroceder a lógicas de WordPress heredadas.

---

## [05 de Septiembre 2026] - Metodología de Inteligencia Artificial (Antigravity)
- **Decisión:** Separación estricta de responsabilidades en conversaciones (ej. una pestaña de chat para Diseño UI/UX y otra para Programación Backend), unificadas a través de un único archivo `AGENTS.md`.
- **Razón:** Prevenir el límite de tokens (pérdida de memoria a corto plazo) y evitar que la IA mezcle contextos visuales con lógicas de bases de datos, manteniendo un flujo de desarrollo altamente profesional.

---

## [06 de Septiembre 2026] - Gestión de Imágenes del Blog
- **Decisión:** Las imágenes de los artículos generados por IA se subirán y asignarán de forma manual por el administrador.
- **Razón:** Los generadores de imágenes aleatorias (como loremflickr) producían imágenes no relacionadas (ej. fotos de montañas para vinilos) que perjudicaban la calidad premium que requiere el blog. La carga manual desde el panel CMS garantiza máxima relevancia visual (Opción A).

---

## [06 de Septiembre 2026] - Modelo Base de IA Backend
- **Decisión:** Uso estricto y exclusivo del modelo `gemini-3.6-flash` para la generación de artículos y cualquier llamada a la API de GenAI dentro de `main.py`.
- **Razón:** Versiones anteriores (como `gemini-1.5-flash` o `1.5-pro`) fueron deprecadas en nuestro entorno o demostraron ser inestables causando errores de timeout 404 y colapsando el Nginx. Esta directiva es estricta para ahorrar tokens y tiempo de debugeo en el futuro. Queda PROHIBIDO usar la versión 1.5.


---

## [21 de Septiembre 2026] - Corrección de modelo en seo_agent.py
- **Decisión:** Se corrigió `seo_agent.py` línea 56: `gemini-1.5-flash` → `gemini-3.6-flash`.
- **Razón:** El script standalone de publicación SEO estaba violando la directiva del 06/09/2026. Fue detectado durante la auditoría de código que generó el archivo `.agents/AGENTS.md`. Esta corrección alinea ambos módulos (`seo_agent.py` y `seo_service.py`) con el modelo obligatorio.

---

## [21 de Septiembre 2026] - Creación del archivo AGENTS.md
- **Decisión:** Se creó `.agents/AGENTS.md` como documento maestro de contexto para todos los agentes de IA.
- **Razón:** El proyecto no tenía un archivo de gobierno agentico centralizado. El `README.md` lo referenciaba pero nunca fue creado. Sin este archivo, cada conversación nueva con la IA parte de cero, generando pérdida de contexto, decisiones inconsistentes y vibe coding de prueba/error. El `AGENTS.md` es la única fuente de verdad: stack, convenciones, prohibiciones, flujo SDD y patrones multiagente.


---

## [21 de Septiembre 2026] - SDD Ciclo 1: Creación de utils.py
- **Decisión:** Se creó `utils.py` con la función `slugify()` centralizada con soporte Unicode completo.
- **Razón:** `slugify()` estaba definida 3 veces inline dentro de funciones en `main.py` (antipatrón). Se extrajo a `utils.py` usando `unicodedata.normalize("NFKD")` para soporte de caracteres españoles (á, ñ, etc.). El output para texto ASCII es retrocompatible con la versión anterior.
- **Archivos afectados:** `utils.py` (creado), `main.py` (3 definiciones eliminadas, import agregado al tope).
- **Verificación:** `main.py` importa sin errores. Servidor responde HTTP 200.

---

## [21 de Septiembre 2026] - Warning crítico: google-generativeai deprecado
- **Decisión:** El paquete `google.generativeai` está deprecado. Migrar a `google.genai` en el próximo ciclo SDD dedicado.
- **Razón:** Al correr la verificación del SDD Ciclo 1, uvicorn emitió un `FutureWarning` indicando que `google.generativeai` ya no recibe actualizaciones ni bugfixes. El nuevo paquete es `google-genai` (sin `ative`). Esta migración requiere cambios en `main.py`, `seo_service.py` y `seo_agent.py`. **No hacer hasta tener un ciclo SDD dedicado** — riesgo de breaking change.

---

## [21 de Septiembre 2026] - Eliminación Definitiva de WordPress (Arquitectura SSG para Blog SEO)
- **Decisión:** Se abandona cualquier integración o idea de usar WordPress para el sitio satélite `oficiocarteleria.com.ar`. En su lugar, el sistema usará una arquitectura de Static Site Generation (SSG). FastAPI generará los archivos `.html` crudos y Nginx los servirá directamente desde una carpeta en el VPS.
- **Razón:** El código antiguo en `seo_agent.py` y `seo_service.py` estaba alucinando integraciones con la API de WordPress, lo cual no era el plan real del usuario. Al cambiar a archivos estáticos locales, evitamos problemas de seguridad, bases de datos innecesarias y maximizamos la velocidad SEO. El registro del dominio no bloquea este desarrollo, ya que puede probarse en directorios locales.

---
*Regla para la IA: Cada vez que el usuario tome una decisión estratégica (Ej. elegir un framework, decidir una pasarela de pago, cambiar el enfoque), debes documentarla aquí añadiendo la fecha, la decisión y el razonamiento.*



## [21 de Septiembre 2026] - SDD Ciclo 3: Refactorización de main.py
- **Decisión:** Se refactorizó `main.py` (de ~1900 líneas a ~40 líneas) dividiendo las rutas en módulos funcionales dentro de un nuevo directorio `routes/`.
- **Razón:** El archivo principal se había vuelto inmanejable. Según las directivas de `AGENTS.md`, se debían agrupar las rutas. Para no romper los templates HTML del frontend modificando las URLs, se optó por crear routers (`APIRouter`) separados lógicamente (`auth.py`, `ui.py`, `v2.py`, `cotizador_api.py`, `catalog_api.py`, `marketing_api.py`, `clientes_api.py`, `media_api.py`, `webhook.py`) pero conservando las mismas rutas (endpoints) originales. Las variables de configuración y funciones compartidas (`get_current_user`, `sessions`, `USERS`) se extrajeron a un nuevo archivo `dependencies.py`.
- **Archivos afectados:** `main.py` (reducido), `dependencies.py` (creado), múltiples archivos en `routes/` (creados).
- **Verificación:** FastAPI inicia correctamente sin errores de dependencias circulares.

---

## [21 de Septiembre 2026] - SDD Ciclo 4: Separación de dependencias de testing
- **Decisión:** Se creó el archivo `requirements-dev.txt` para incluir las dependencias exclusivas de testing (`pytest`, `httpx`, `pytest-asyncio`), separándolas de `requirements.txt`.
- **Razón:** Mantener el entorno de producción limpio y ligero, instalando únicamente los paquetes necesarios para que la aplicación funcione. Las dependencias de testing solo se instalan en entornos locales de desarrollo o CI/CD, mejorando la seguridad y optimizando el tamaño del deployment.
- **Archivos afectados:** `requirements-dev.txt` (creado), `AGENTS.md` (actualizado).

---

## [21 de Septiembre 2026] - SDD Ciclo 5: Implementación de CI/CD
- **Decisión:** Se implementó un pipeline de GitHub Actions (`ci-cd.yml`) para ejecutar tests automáticos (pytest en Python 3.13) en la rama `main` y automatizar despliegues al VPS de Donweb mediante `appleboy/ssh-action`. Además, se refactorizaron los scripts de deploy locales (`deploy.exp`, etc.) para leer credenciales desde un archivo `.env.deploy` que fue añadido al `.gitignore`.
- **Razón:** Cumplir estrictamente con la Regla #4 de `AGENTS.md` (PROHIBIDO hardcodear credenciales) y asegurar que el código no llegue a producción sin pasar los tests automatizados previamente.

---

## [21 de Septiembre 2026] - SDD Ciclo 6: Migración de sesiones In-Memory a JWT
- **Decisión:** Se reemplazó el diccionario `sessions = {}` en memoria por JSON Web Tokens (JWT) firmados (`PyJWT`), almacenados en cookies HTTP-only.
- **Razón:** La implementación de CI/CD (Ciclo 5) provocaba que el servidor se reiniciara con cada despliegue, perdiendo el estado en memoria y deslogueando a los usuarios activos (vendedores en mostrador, administrador). JWT hace que la autenticación sea "stateless" (sin estado en memoria), manteniendo activas las sesiones a través de reinicios del servidor. Se conservó compatibilidad completa con el objeto `user` inyectado a los templates Jinja2.
- **Archivos afectados:** `requirements.txt`, `.env.example`, `dependencies.py`, `routes/auth.py`, `tests/test_cotizador.py`, `tests/test_catalog.py`.

---

## [21 de Septiembre 2026] - SDD Ciclo 8: Vista individual de productos en Tienda V2 y Manejo de Error 404
- **Decisión:** Implementación de la ruta `/v2/producto/{id}` renderizada del lado del servidor (SSR) mediante `v2_product.html`, retornando un código de estado `404` estricto en caso de que el producto no exista en lugar de un redireccionamiento `RedirectResponse`.
- **Razón:** La tienda V2 carecía de vistas individuales para los productos. Se eligió mantener SSR (sin frameworks SPA) de acuerdo con las restricciones arquitectónicas del proyecto (ver AGENTS.md). Se forzó un 404 estricto para evitar un "Soft 404" (lo que penalizaría el posicionamiento en Google). La plantilla 404 guía al usuario nuevamente al catálogo sin impactar el SEO negativamente.
- **Archivos afectados:** `routes/v2.py` (modificado), `templates/v2_product.html` (creado), `templates/v2_404.html` (creado).

---

## [21 de Septiembre 2026] - SDD Ciclo 10: Buscador Global Tienda V2
- **Decisión:** Se implementó una barra de búsqueda global en la página de inicio que filtra sobre todo el catálogo y muestra resultados en una nueva vista dedicada (`v2_search.html`).
- **Razón:** Facilitar la localización rápida de productos mediante código o nombre. El frontend mantiene estricta compatibilidad con las reglas del proyecto (Renderizado en servidor y vanilla JS para funciones interactivas del carrito) y hereda la navegabilidad lograda en el Ciclo 9 para acceder al detalle de productos.
- **Archivos afectados:** `routes/v2.py` (modificado), `templates/v2_home.html` (modificado), `templates/v2_search.html` (creado).

---

## [21 de Septiembre 2026] - SDD Ciclo 11: Generador SSG Blog (oficiocarteleria.com.ar)
- **Decisión:** Se refactorizó la lógica de generación del blog SEO satélite (`seo_service.py`) integrando el manejo robusto de excepciones del SDK `google-genai` y asegurando la escritura local de archivos HTML. Adicionalmente, el template `v2_blog_post.html` se convirtió en un documento HTML *standalone* (independiente).
- **Razón:** Para el sitio satélite (`oficiocarteleria.com.ar`) servido como SSG puro, heredar del layout principal de FastAPI (`v2_base.html`) ocasionaba dependencias dinámicas, problemas de resolución de rutas relativas a los assets estáticos de la app principal, y enlaces conflictivos. Convertir el template en independiente asegura que los archivos generados funcionen correctamente y de forma optimizada para SEO al servirse en un dominio satélite ajeno.
- **Archivos afectados:** `seo_service.py` (modificado), `templates/v2_blog_post.html` (modificado).

---

## [21 de Septiembre 2026] - SDD Ciclo 12: Refactor Marketing IA y Rediseño CSS
- **Decisión:** Se eliminó el scraping de YouTube, se neutralizaron los prompts de la IA para eliminar el sesgo comercial hacia Orafol, y se rediseñó `v2_blog_post.html` usando CSS puro inspirado en plataformas de lectura (Medium).
- **Razón:** El scraping de YouTube no aportaba valor textual útil para la generación de artículos. Los prompts de la IA sesgaban comercialmente el contenido, restando profesionalismo. El rediseño CSS optimiza la experiencia de lectura (max-width 800px, font 20px, texto #242424) haciéndola más atractiva sin requerir frameworks pesados.
- **Archivos afectados:** `routes/marketing_api.py` (modificado), `templates/v2_blog_post.html` (modificado).

---

### SDD Ciclo 16 — 22/09/2026
**Decisión:** Se actualizó la lógica de recomendación de "Productos Relacionados" (También podrías necesitar).
**Razón:** El sistema anterior solo permitía agrupar productos por la Categoría principal, lo cual generaba sugerencias poco precisas cuando una misma categoría (ej. "Vinilos para impresión") contenía subcategorías muy distintas (ej. "DPI" vs "Orajet").
**Detalles:** Se modificó `routes/v2.py` para que el algoritmo busque primero si existe una regla en `categorias_meta.json` usando el "slug" de la **Subcategoría** del producto. Si no la encuentra, hace fallback al slug de la Categoría principal, y si tampoco la encuentra, hace fallback a 4 productos al azar de su misma familia.

## [21 de Septiembre 2026] - SDD Ciclo 13: Toques Finales Módulo Marketing IA
- **Decisión:** Se forzó el uso de etiquetas HTML en el CTA del prompt de Gemini y se implementó un sistema de shortcodes de imágenes vía regex. Además se mejoró visualmente la grilla del blog frontend usando CSS moderno.
- **Razón:** Para asegurar que los enlaces generados sean clickeables automáticamente, poder embeber imágenes con facilidad en medio del contenido generado por IA y proveer una experiencia visual de alta calidad a los usuarios del blog.
- **Archivos afectados:** `routes/marketing_api.py`, `templates/v2_blog.html`, `templates/v2_blog_post.html`.

---

## [21 de Septiembre 2026] - SDD Ciclo 14: Estandarización de Imágenes y Preview UI
- **Decisión:** Se implementó una arquitectura estilo CMS para el manejo de shortcodes: se mantienen crudos (`[FOTO: x.jpeg]`) en la base de datos y se parsean con RegEx únicamente al momento de visualización (Preview y SSG). Las imágenes embebidas se limitaron a 200px (centradas) y la imagen de portada a 400px (object-fit: cover). El endpoint de imágenes se hizo case-insensitive.
- **Razón:** Para prevenir que los shortcodes se destruyan permanentemente en la base de datos al momento del guardado, alinear el comportamiento con las expectativas del usuario, evitar imágenes rotas por discrepancias de mayúsculas en Linux, y asegurar un diseño limpio y centrado tipo "tarjeta" en la vista previa del administrador.
- **Archivos afectados:** `routes/marketing_api.py`, `routes/media_api.py`, `seo_service.py`, `templates/v2_blog_post.html`.

---

## [22 de Septiembre 2026] - SDD Ciclo 15: Restauración de Productos Relacionados en Tienda V2
- **Decisión:** Se restauró la lógica de "Productos Relacionados" (fallback a la misma categoría si no hay datos en `categorias_meta.json`) y se refactorizó el CSS a un bloque estilo Grid responsive.
- **Razón:** El archivo de producción había sido sobreescrito accidentalmente durante un deploy previo. Se re-implementó asegurando un diseño adaptable en móviles y escritorio (`minmax(150px, 1fr)`).
- **Archivos afectados:** `routes/v2.py`, `templates/v2_product.html`.

---

## [23 de Septiembre 2026] - SDD Ciclo 17: Implementación del Módulo de Clientes
- **Decisión:** Se implementó el alta, edición e importación de clientes mediante CSV. Se migró la base de datos `clientes` agregando las columnas necesarias para el mapeo con el sistema SaaS heredado y se creó un modal Vanilla JS para ABM de clientes en el frontend.
- **Razón:** Proveer a los vendedores la capacidad de gestionar la base de clientes y unificar el directorio, permitiendo además la transición desde el SaaS legacy mediante importación por lotes. Se mantuvo el uso de Vanilla JS y renderizado de plantillas cumpliendo la arquitectura estipulada.
- **Archivos afectados:** `routes/clientes_api.py`, `templates/clientes.html`, `data/disgraf_hub.db` (migración de esquema).

---

## [23 de Septiembre 2026] - SDD Ciclo 17.1: Ajuste Fino Condiciones Comerciales
- **Decisión:** Se agregaron 3 columnas de reglas de negocio (`lista_de_precio`, `permite_cuenta_corriente`, `limite_cuenta_corriente`) a la tabla `clientes`, modificando el endpoint y el frontend. Se eliminó el campo desplegable "Categoría" en la vista.
- **Razón:** Para soportar la lógica de negocio de Cuentas Corrientes y Listas de Precio que diferenciarán a los clientes mayoristas de los minoristas, alineándose con las directivas del Coordinador.
- **Archivos afectados:** `routes/clientes_api.py`, `templates/clientes.html`, `data/disgraf_hub.db` (migración de esquema).

---

## [23 de Septiembre 2026] - Ajuste rápido
- **Decisión:** Se agregó el botón "Exportar CSV" en la vista del Gestor de Catálogos (`precios.html`) con un endpoint asociado `GET /api/export-maestro` en `routes/catalog_api.py`.
- **Razón:** Permitir a los usuarios descargar el archivo maestro de productos (CSV) para modificar masivamente descripciones o stocks desde herramientas externas (como Excel) y luego re-importarlo mediante el flujo existente.
- **Archivos afectados:** `routes/catalog_api.py`, `templates/precios.html`.

---

## [23 de Septiembre 2026] - Corrección de bug en importación CSV
- **Decisión:** Se implementó autodetección dinámica del delimitador (`,` o `;`) y validación estricta de columnas obligatorias (`Nº de producto`, `Nombre`) al procesar subidas en `api_upload_saas` (`routes/catalog_api.py`).
- **Razón:** Cuando los usuarios editaban el archivo CSV exportado usando Microsoft Excel y lo volvían a guardar, el programa cambiaba silenciosamente el delimitador de `;` a `,`, provocando que Pandas no pudiera parsear el archivo con el `sep=';'` hardcodeado.
- **Archivos afectados:** `routes/catalog_api.py`.
