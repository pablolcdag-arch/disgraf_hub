# Disgraf Hub - Sistema de Gestión V2

Este archivo documenta la visión, el estado actual y el mapa de ruta (roadmap) de **Disgraf Hub**, una plataforma integral en desarrollo que servirá como ERP, E-commerce, y CRM para **Disgraf Insumos Gráficos**.

## 🎯 Objetivo General del Proyecto

El objetivo principal de Disgraf Hub es **reemplazar el sistema actual (SAAS Argentina)** con una solución a medida mucho más potente, conectada y moderna, desarrollando simultáneamente la **Versión 2 (V2)** de la página web.

Este sistema debe centralizar todas las operaciones de la empresa, desde la venta en mostrador hasta la generación de tráfico orgánico mediante IA.

## 📦 Módulos Actuales (En desarrollo / Funcionando)

### 1. Cotizador para Vendedores (Mostrador)
Una herramienta de uso interno para que los vendedores en el local físico puedan generar presupuestos rápidos y en formato PDF.
- **Archivos Clave:** `cotizador.html`, `precios.html`, `clientes.html`.
- **Estado:** Funcionando con historial de cotizaciones y descarga de PDFs.

### 2. Tienda V2 (Catálogo Público)
El storefront público para los clientes de Disgraf.
- **Archivos Clave:** `v2_home.html`, `v2_category.html`.
- **Estado:** En desarrollo.

### 3. Marketing IA (SEO Satélite)
Un dashboard administrativo que utiliza Inteligencia Artificial (Gemini Pro) para generar artículos de blog automáticos.
- **Archivos Clave:** `marketing.html`, `v2_blog.html`, `v2_blog_post.html`.
- **Estrategia SEO:** Estos artículos **no** se alojan en `disgraf.com.ar`. Se suben a un dominio "satélite" e independiente (`oficiocarteleria.com.ar`) que funciona como una revista del rubro para recomendar sutilmente a Disgraf y generar backlinks valiosos de alta autoridad.

### 4. Sincronizador de Datos
Módulo y botón en el dashboard para mantener la información actualizada.
- **Estado:** Operativo y alimentando la plataforma V2.

## 🚀 Roadmap Futuro (Hitos a largo plazo)

Para lograr el reemplazo total de SAAS Argentina, el proyecto escalará con los siguientes módulos clave:

1. **Integración con ARCA (ex AFIP):** 
   - Conexión oficial para la emisión de facturación electrónica de manera automatizada.
2. **Gestión Financiera (Cuentas Corrientes):** 
   - Importación y control absoluto de los saldos, débitos y créditos de los clientes y proveedores.
3. **Múltiples Medios de Pago:** 
   - Soporte nativo para E-cheqs, Cheques físicos, Transferencias bancarias, y conciliación de Cajas de los locales.

## 💻 Arquitectura Técnica

- **Backend:** Python + FastAPI.
- **Frontend:** Jinja2 + HTML/CSS Puro + Javascript Vainilla.
- **Servidor (Producción):** VPS Ubuntu alojado en Donweb.
  - El despliegue de código a la VPS (subida de archivos y reinicio de la app) está completamente automatizado a través de un script en la Mac local llamado `deploy.exp`.

## 🎨 Sección de Diseño (UI/UX)
El desarrollo visual de la V2 se lleva a cabo en conversaciones separadas para no mezclar la lógica de Python con el diseño frontend. 
- **Estado Actual del Diseño:** (A completar por el agente de diseño). Todo el diseño visual, paletas de colores y estilos deben registrarse aquí para mantener coherencia.

---
## ⚠️ REGLAS OBLIGATORIAS PARA CUALQUIER AGENTE DE IA
1. **Actualización Obligatoria:** Después de cada modificación arquitectónica o cambio de rumbo del proyecto, el agente **DEBE** actualizar inmediatamente este archivo `README.md` y sincronizarlo con `.agents/AGENTS.md`.
2. **Bitácora de Decisiones:** Cualquier decisión estratégica (ej. cambio de dominio, elección de framework, descarte de una tecnología) debe registrarse obligatoriamente en `decisions_log.md` detallando el motivo.
3. **Despliegue:** Al modificar código local, se debe activar la skill `deploy-donweb` para reflejar los cambios en producción.
4. **Sinergia:** Todas las conversaciones comparten este mismo archivo de contexto. ¡No crees archivos de reglas duplicados!
