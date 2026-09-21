# SPEC — utils.py (SDD Ciclo 1)
> Fecha: 21/09/2026 | Estado: APROBADO

## Qué queremos

Crear el archivo `utils.py` en la raíz del proyecto con las funciones utilitarias compartidas
que hoy están duplicadas o definidas dentro de funciones en `main.py`.

## Problema actual

`main.py` tiene los siguientes antipatrones detectados en la auditoría:

| Antipatrón | Ocurrencias | Líneas ejemplo |
|---|---|---|
| `def slugify()` definida dentro de función | 3 veces | 163, 305, 1184 |
| `import re` dentro de función | 4+ veces | 162, 254, 304, 1096 |
| `import json` dentro de función | 15+ veces | 180, 441, 531, 640... |
| `import os` dentro de función | 8+ veces | 222, 359, 463... |
| `import pandas as pd` dentro de función | 4+ veces | 223, 357, 462 |
| `bare except:` sin tipo | 12+ veces | 187, 233, 250, 376... |

## Criterios de Aceptación

- [x] Existe `utils.py` en la raíz del proyecto
- [x] `slugify()` definida UNA SOLA VEZ en `utils.py`
- [x] Las 3 definiciones inline de `slugify` en `main.py` eliminadas
- [x] `main.py` importa `slugify` desde `utils` al tope del archivo
- [x] Los 3 endpoints que usaban `slugify` local ahora usan la importada
- [x] La app arranca sin errores (`uvicorn main:app`)
- [x] Endpoint `/v2/categoria/{slug}` sigue funcionando

## Fuera de scope (ciclo 1)

- NO tocar los imports dentro de funciones todavía (son 30+, eso es otro ciclo)
- NO refactorizar los bare except todavía
- NO mover otras funciones a utils.py todavía

## Riesgo

**Bajo.** Solo se elimina código duplicado. La función `slugify` es pura (sin side effects).

