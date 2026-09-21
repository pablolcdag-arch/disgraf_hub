# AGENTS.md — Disgraf Hub
> **Documento Maestro de Contexto para Agentes de IA**
> Versión: 1.0 | Última actualización: 21/09/2026
> **Este archivo es la fuente única de verdad para cualquier agente que trabaje en este proyecto.**
> Antes de escribir una sola línea de código, leer este archivo completo.

---

## 📌 REGLA NÚMERO UNO

> **LEE TODO ESTE ARCHIVO ANTES DE HACER CUALQUIER COSA.**
> Si una directiva aquí contradice algo que el usuario dice en el chat, **este archivo tiene prioridad** y debes señalarlo antes de proceder.

---

## 🏢 Contexto del Negocio

**Empresa:** Disgraf Insumos Gráficos (Argentina)
**Dominio principal:** `disgraf.com.ar`
**Dominio satélite (blog SEO):** `oficiocarteleria.com.ar`
**Rubro:** Venta de insumos gráficos — vinilos de corte, ORACAL, materiales de impresión, cartelería, herrajes, laminados.
**Operación:** Local físico con vendedores en mostrador + venta online (en desarrollo).

**Sistema que se está reemplazando:** SAAS Argentina (ERP/facturación legacy).
**Objetivo a largo plazo:** Disgraf Hub = ERP + E-commerce + CRM completamente propio.

---

## 🎯 Visión del Producto

Disgraf Hub es una plataforma integral que centraliza:
1. **Cotizador para vendedores** — presupuestos en PDF para el mostrador
2. **Tienda V2 (Catálogo público)** — storefront para clientes
3. **Marketing IA (SEO satélite)** — generación automática de artículos vía Gemini
4. **Panel de administración** — gestión de precios, productos, media
5. **Sincronizador de datos** — mantiene catálogo actualizado desde CSV de SAAS Argentina

**Módulos futuros:** Facturación electrónica ARCA (ex-AFIP), Cuentas Corrientes, Medios de Pago múltiples, Cheques electrónicos.

---

## 💻 Stack Tecnológico

### Backend
- **Lenguaje:** Python 3.14
- **Framework:** FastAPI `>=0.111.0`
- **Servidor ASGI:** Uvicorn `>=0.23.0`
- **Templating:** Jinja2 (server-side rendering)

### Frontend
- **Templates:** HTML + CSS Puro + JavaScript Vanilla
- **Sin frameworks frontend** (no React, no Vue, no Tailwind CDN en prod)
- **Renderizado:** Jinja2 server-side, sin SPA

### Base de Datos
- **Motor:** SQLite (`data/disgraf_hub.db`)
- **ORM:** Ninguno — queries SQL directas o pandas para CSV
- **Datos CSV:** `data/maestro_productos.csv` (catálogo SAAS) y `data/productos_seleccionados.csv` (curacion manual)

### Dependencias clave
```
fastapi>=0.111.0
uvicorn>=0.23.0
pandas>=1.3.0
reportlab>=3.6.0       # Generación de PDFs
python-multipart>=0.0.5
python-dotenv>=0.20.0
requests>=2.26.0
jinja2
google-genai            # SDK oficial Google Gemini (migrado desde google-generativeai deprecado — SDD Ciclo 2, 21/09/2026)
```

### Inteligencia Artificial
- **Proveedor:** Google Gemini via `google-genai` SDK (v2.24.0+)
- **Modelo OBLIGATORIO:** `gemini-3.6-flash`
- **PROHIBIDO:** cualquier versión `1.5-*` (causó errores 404 y colapso de Nginx)
- **PROHIBIDO:** usar el paquete `google-generativeai` — está DEPRECADO. Usar siempre `google-genai`.
- **Uso:** Generación de artículos SEO en HTML para WordPress; asistente Telegram
- **Patrón canónico obligatorio:**
  ```python
  from google import genai
  gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
  # Uso:
  response = gemini_client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
  text = response.text
  ```
- **Migración completada:** SDD Ciclo 2 — 21/09/2026 ✅


### Infraestructura
- **Servidor Producción:** VPS Ubuntu — proveedor Donweb
- **Proxy inverso:** Nginx (maneja SSL y ruteo a uvicorn)
- **Proceso:** uvicorn corriendo como servicio systemd
- **Deploy:** Script `deploy.exp` (Expect/SSH) ejecutado desde Mac local

### Notificaciones
- **Canal:** Telegram Bot API
- **Variable de entorno:** `TELEGRAM_TOKEN`

### Integración WordPress (blog satélite)
- **Sitio:** `oficiocarteleria.com.ar`
- **API:** WordPress REST API v2 (`/wp-json/wp/v2/posts`)
- **Auth:** Application Password (Basic Auth)

---

## 📁 Estructura del Proyecto

```
Disgraf_Hub/
├── .agents/
│   └── AGENTS.md          ← ESTE ARCHIVO (fuente de verdad)
├── .env                   ← Variables de entorno (NO commitear)
├── .env.example           ← Template de variables (SÍ commitear)
├── README.md              ← Visión general y roadmap (sincronizar con este archivo)
├── decisions_log.md       ← Bitácora de decisiones estratégicas
├── requirements.txt       ← Dependencias Python de producción
├── requirements-dev.txt   ← Dependencias Python de desarrollo y testing (pytest, httpx)
├── utils.py               ← Funciones utilitarias compartidas (slugify, etc.)

├── main.py                ← Aplicación principal FastAPI (Refactorizado, inicializa routers)
├── dependencies.py        ← Dependencias compartidas (sesiones, config, auth mock)
├── routes/                ← Directorio de módulos/routers de FastAPI (ui, api, auth, etc.)
├── seo_service.py         ← Lógica de generación y publicación de artículos SEO
├── seo_agent.py           ← Script standalone para publicación (ATENCIÓN: revisar modelo)
├── test_gemini.py         ← Test básico de conectividad con Gemini API
├── deploy.exp             ← Script de deploy automático a VPS (Expect/SSH)
├── check_logs.exp         ← Script de verificación de logs en VPS
├── deploy_fix.exp         ← Variante de deploy para correcciones urgentes
├── data/
│   ├── disgraf_hub.db          ← Base de datos SQLite principal
│   ├── maestro_productos.csv   ← Catálogo completo exportado de SAAS Argentina (separador: ;)
│   ├── productos_seleccionados.csv ← Selección curada para la tienda V2
│   ├── categorias_meta.json    ← Metadatos de categorías del catálogo
│   ├── historial_presupuestos.json ← Historial de cotizaciones generadas
│   ├── marketing_config.json   ← Configuración del módulo de marketing IA
│   └── marketing_content.json  ← Contenido generado por el módulo de marketing
├── templates/                  ← Templates Jinja2 (HTML)
│   ├── base.html               ← Layout base (header, nav, footer)
│   ├── login.html              ← Pantalla de login
│   ├── dashboard.html          ← Panel de administración principal
│   ├── cotizador.html          ← Herramienta de presupuestos para vendedores
│   ├── precios.html            ← Gestión de precios (solo admin)
│   ├── clientes.html           ← Gestión de clientes
│   ├── marketing.html          ← Dashboard de marketing IA
│   ├── media.html              ← Gestión de imágenes/media
│   ├── storefront.html         ← Tienda pública (v1, legacy)
│   ├── satellite_demo.html     ← Demo del sitio satélite SEO
│   ├── v2_base.html            ← Layout base de la V2
│   ├── v2_home.html            ← Home de la tienda V2
│   ├── v2_category.html        ← Página de categoría V2
│   ├── v2_blog.html            ← Blog (headless, sin rutas públicas activas)
│   └── v2_blog_post.html       ← Post individual del blog
├── static/                     ← Assets estáticos (CSS, JS, imágenes)
├── assets/                     ← Recursos de la aplicación
└── venv/                       ← Entorno virtual Python (NO tocar, NO commitear)
```

---

## 🔑 Variables de Entorno

Todas las variables sensibles van en `.env`. **NUNCA hardcodear credenciales en el código.**

```bash
# API Keys
GEMINI_API_KEY=         # Google Gemini API key

# Telegram
TELEGRAM_TOKEN=         # Bot token de Telegram

# WordPress (sitio satélite)
WP_URL=                 # URL base del sitio WP (ej: https://oficiocarteleria.com.ar)
WP_USER=                # Usuario WP con rol Editor/Admin
WP_APP_PASSWORD=        # Application Password generada desde WP

# Autenticación interna
ADMIN_USERNAME=         # Usuario administrador
ADMIN_PASSWORD=         # Contraseña admin
SELLER_USERNAME=        # Usuario vendedor
SELLER_PASSWORD=        # Contraseña vendedor

# Directorios
DATA_DIR=./data         # Directorio de datos (default: ./data)
```

---

## 🏗️ Convenciones de Código

### Python General
- **Estilo:** PEP 8
- **Indentación:** 4 espacios (nunca tabs)
- **Strings:** comillas dobles `"` para strings regulares, `f-strings` para interpolación
- **Imports:** siempre al tope del archivo, agrupados: stdlib → third-party → local. **NUNCA imports dentro de funciones** (antipatrón existente en main.py a corregir)
- **Manejo de errores:** `except Exception as e:` con log del error. **NUNCA** `bare except:` sin capturar el tipo

### Funciones y Módulos
- Funciones de utilidad compartida van en un archivo `utils.py` (pendiente crear)
- Funciones que se repiten en más de un lugar → extraer inmediatamente a utilidades
- Una función = una responsabilidad

### Rutas FastAPI
- Agrupar rutas por dominio funcional con prefijo: `/cotizador`, `/v2`, `/admin`, etc.
- Siempre verificar autenticación al inicio del endpoint con `get_current_user()`
- Redireccionar a `/` si no hay sesión, nunca devolver 403 sin HTML

### Templates Jinja2
- Usar herencia de templates: todos extienden `base.html` o `v2_base.html`
- Variables de contexto en snake_case
- Lógica mínima en templates — la lógica de negocio va en Python

### Datos CSV
- Separador: `;` (punto y coma)
- Encoding principal: `utf-8` con fallback a `latin-1`
- Columnas clave del maestro: `Nº de producto`, `Nombre`, `Precio ($)`, `Unidad`

### Naming
- Variables y funciones: `snake_case`
- Constantes globales: `UPPER_SNAKE_CASE`
- Templates HTML: `nombre_modulo.html` (snake_case)
- Archivos Python: `nombre_modulo.py` (snake_case)

---

## 🔄 Flujo de Trabajo

### Ciclo de Desarrollo Standard
```
1. LEER este AGENTS.md
2. LEER decisions_log.md (entender qué fue descartado y por qué)
3. ESPECIFICAR la tarea (qué queremos, criterios de aceptación)
4. PLANIFICAR la implementación (cómo, qué archivos tocar)
5. IMPLEMENTAR (escribir el código mínimo necesario)
6. VERIFICAR (test manual o automatizado)
7. ACTUALIZAR este archivo si hubo cambio arquitectónico
8. REGISTRAR en decisions_log.md si hubo decisión estratégica
9. DEPLOY con skill deploy-donweb
```

### Separación de Conversaciones
Para evitar overflow de contexto, cada conversación tiene un foco:
- **Conversación Backend/Python:** lógica de FastAPI, DB, servicios
- **Conversación Diseño/Frontend:** HTML, CSS, UX, templates
- **Conversación Marketing IA:** prompts, SEO, publicación WP

Todas comparten este `AGENTS.md` como contexto unificado.

---

## 🚫 PROHIBICIONES ABSOLUTAS

> [!CAUTION]
> Violar estas reglas genera bugs en producción y fue documentado en decisions_log.md.

1. **PROHIBIDO** usar `gemini-1.5-flash` o cualquier modelo `1.5-*` → usar solo `gemini-3.6-flash`
2. **PROHIBIDO** alojar el blog en `disgraf.com.ar/blog` → solo en `oficiocarteleria.com.ar`
3. **PROHIBIDO** volver a lógicas de WordPress/WooCommerce para el sistema principal
4. **PROHIBIDO** hardcodear credenciales, API keys o contraseñas en el código
5. **PROHIBIDO** crear archivos de reglas duplicados → solo este `AGENTS.md` y `decisions_log.md`
6. **PROHIBIDO** `bare except:` sin capturar el tipo de excepción
7. **PROHIBIDO** usar `allow_origins=["*"]` en producción (corregir cuando se migre a HTTPS propio)
8. **PROHIBIDO** hacer `import` dentro de funciones (limpiar los existentes en main.py)
9. **PROHIBIDO** modificar el directorio `venv/`
10. **PROHIBIDO** commitear el archivo `.env`

---

## 🧪 Testing

### Estado actual
- Suite completa implementada (`test_auth.py`, `test_cotizador.py`, `test_api.py`, `test_seo_service.py`, `test_catalog.py`, `test_gemini.py`).

### Estrategia de Testing (a implementar)
```
tests/
├── test_auth.py          ← Pruebas de login/logout/sesiones
├── test_cotizador.py     ← Generación de PDFs y presupuestos
├── test_seo_service.py   ← Generación de artículos (mock de Gemini API)
├── test_catalog.py       ← Carga y parsing del CSV de productos
└── test_api.py           ← Tests de endpoints FastAPI (httpx + pytest)
```

### Cómo correr tests
```bash
# Desde la raíz del proyecto, con el venv activado:
source venv/bin/activate
pytest tests/ -v

# Test puntual:
pytest tests/test_seo_service.py -v
```

### Criterios de aceptación para deploy
- [ ] App inicia sin errores (`uvicorn main:app`)
- [ ] Login funciona con credenciales de `.env`
- [ ] Endpoint `/cotizador` responde 200
- [ ] Endpoint `/v2` carga el catálogo correctamente
- [ ] `test_gemini.py` pasa sin errores

---

## 🚀 Deploy (CI/CD)

### 1. Despliegue Automático (GitHub Actions)
El proceso de integración y despliegue continuo (CI/CD) está completamente automatizado a través de GitHub Actions.

**Flujo (`.github/workflows/ci-cd.yml`):**
1. Al hacer `push` a la rama `main`, se levanta un entorno virtual (Python 3.13).
2. Se corren todos los tests automáticos (`pytest`).
3. **Sólo si los tests pasan**, se copian los archivos al VPS de Donweb (vía SSH/SCP usando secretos configurados en el repo).
4. Se reinicia automáticamente el servicio `disgraf-hub` de Uvicorn.

### 2. Scripts de Deploy Locales (Fallback)
Si por algún motivo GitHub Actions no está disponible, se pueden usar los scripts manuales.
**⚠️ REGLA DE SEGURIDAD:** Los scripts de expect (`deploy.exp`, `check_logs.exp`, `deploy_fix.exp`) **no deben tener credenciales hardcodeadas**.
Extraen las credenciales locales desde el archivo `.env.deploy` (el cual está excluido en `.gitignore`). Existe un `.env.deploy.example` de referencia.

```bash
# Despliegue local (requiere .env.deploy)
./deploy.exp

# Verificar logs remotamente
./check_logs.exp
```

### ⚠️ Regla de deploy general
Nunca empujar a `main` ni ejecutar `deploy.exp` sin haber verificado localmente que la app inicia y los tests pasan localmente sin errores.

---

## 🤖 Patrones Agenticos

### Modelo de Razonamiento
- **Modelo para todas las tareas:** Claude Sonnet 4.6 (suscripción Pro de Antigravity)
- **Gestión de quota:** No iniciar tareas que no puedan completarse en el turno actual

### Bucle SDD (Especificar → Plan → Tareas → Implementar → Verificar)
Todo desarrollo de features significativas sigue este bucle:

```
1. ESPECIFICAR  → spec_[feature].md con criterios de aceptación
2. PLAN         → implementation_plan.md con decisiones técnicas
3. TAREAS       → task.md con checklist atómico
4. IMPLEMENTAR  → Ejecución (puede usar subagentes)
5. VERIFICAR    → Tests + revisión de criterios
   └── ¿Pasa? → SÍ: actualizar AGENTS.md + decisions_log, hacer deploy
              → NO: volver a ESPECIFICAR con el diagnóstico del fallo
```

### Flujo Multiagente
Cuando una tarea es compleja, usar el siguiente patrón:

| Agente | Rol | Puede escribir código |
|---|---|---|
| **Coordinador** | Lee la tarea, la divide, asigna subtareas | ❌ No |
| **Investigador** | Lee archivos, inspecciona DB, audita código | ❌ No |
| **Implementador A/B/C** | Ejecuta una subtarea acotada | ✅ Sí |
| **Verificador** | Corre tests, revisa que cumple la spec | ❌ No |

**Regla:** Si el Verificador falla 3 veces en la misma subtarea → escalar al usuario con diagnóstico.

### MCPs Disponibles
- **Context7:** Documentación actualizada de librerías en tiempo real (FastAPI, google-generativeai)
- **SQLite MCP:** Inspección directa de `disgraf_hub.db` sin escribir Python

---

## 📋 Estilo de Commits

```
tipo(scope): descripción en imperativo en español

tipos: feat | fix | refactor | docs | style | test | deploy | chore

Ejemplos:
feat(cotizador): agregar campo de descuento por cantidad
fix(seo): corregir modelo gemini a 3.6-flash
docs(agents): actualizar stack tecnológico con nueva dependencia
deploy(vps): aplicar corrección de Nginx para SSL
refactor(main): extraer lógica del cotizador a routes/cotizador.py
```

### Reglas de PR (cuando se incorpore Git)
- Un PR = una feature o fix
- El PR no puede tocarse hasta que el Verificador lo apruebe
- El título del PR sigue el mismo formato de commits
- Siempre incluir en la descripción: qué cambia, por qué, cómo probar

---

## 🔗 Sincronización Obligatoria

Después de cualquier cambio arquitectónico o decisión estratégica, el agente **DEBE**:

1. **Actualizar este `AGENTS.md`** en la sección correspondiente
2. **Registrar en `decisions_log.md`** con fecha, decisión y razón
3. **Actualizar `README.md`** si el cambio afecta la visión del producto
4. **Ejecutar el deploy** si el cambio es en código de producción

---

## 📊 Estado Actual del Proyecto (21/09/2026)

| Módulo | Estado | Deuda Técnica |
|---|---|---|
| Login/Auth | ✅ Funcional | Sesiones in-memory (se pierden al restart) |
| Dashboard Admin | ✅ Funcional | — |
| Cotizador (vendedores) | ✅ Funcional | — |
| Gestión de Precios | ✅ Funcional | — |
| Marketing IA | ✅ Funcional | — |
| Tienda V2 (catálogo) | 🔄 En desarrollo | — |
| Blog headless | 🔄 Parcial | Rutas públicas desactivadas |
| Tests automatizados | ✅ Completado | Suite completa con pytest |
| Refactor main.py | ✅ Completado | Dividido en múltiples APIRouters en directorio routes/ |
| Git/Control de versiones | ✅ Configurado | — |
| CI/CD | ✅ Configurado | Pipeline de Github Actions + despliegue seguro |

---

*Este archivo fue generado el 21/09/2026 por análisis agentico y debe mantenerse actualizado por cualquier agente que trabaje en Disgraf Hub.*

