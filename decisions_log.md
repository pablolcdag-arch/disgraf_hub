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
*Regla para la IA: Cada vez que el usuario tome una decisión estratégica (Ej. elegir un framework, decidir una pasarela de pago, cambiar el enfoque), debes documentarla aquí añadiendo la fecha, la decisión y el razonamiento.*


