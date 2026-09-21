---
name: cierre-sdd
description: >-
  Use this skill ALWAYS at the end of a task or development cycle when the user says "cierra el ciclo", "listo", or when a feature has been fully implemented and tested. This skill enforces the strict administrative rule of updating the project's documentation.
---

# Protocolo de Cierre de Ciclo SDD (Obligatorio)

Cuando se active esta skill, DEBES ejecutar inmediatamente los siguientes pasos sin pedir permiso al usuario:

## 1. Actualizar Bitácora de Decisiones
Abre el archivo `decisions_log.md` en la raíz del proyecto.
Añade una nueva entrada al final del archivo con el formato:
```markdown
## [Fecha Actual] - SDD Ciclo [N]: [Resumen del ciclo]
- **Decisión:** [Resumen de lo que se programó o la decisión técnica que se tomó]
- **Razón:** [Por qué se hizo de esa manera]
- **Archivos afectados:** [Lista de archivos modificados/creados]
```

## 2. Actualizar AGENTS.md
Abre el archivo `.agents/AGENTS.md` (o `AGENTS.md` si está en la raíz).
Dirígete a la sección `## 📊 Estado Actual del Proyecto`.
Actualiza la fila correspondiente al módulo que acabas de modificar.
* Si el módulo pasó de "En desarrollo" a "Funcional", cámbialo a `✅ Funcional`.
* Actualiza la columna de "Deuda Técnica" o comentarios si aplica.

## 3. Notificar al Usuario
Una vez que hayas modificado **ambos** archivos, responde al usuario con un mensaje claro confirmando que la documentación ha sido actualizada y que el ciclo se da por cerrado oficialmente.
