# PLAN — utils.py (SDD Ciclo 1)
> Fecha: 21/09/2026

## Decisiones técnicas

- `utils.py` va en la raíz del proyecto (mismo nivel que `main.py`)
- `slugify` necesita manejar caracteres especiales del español (á, é, ñ, etc.) → usar `unicodedata`
- El import en `main.py` va al tope, grupo "local" → `from utils import slugify`

## Archivos a crear

### [NEW] utils.py
Contendrá `slugify(text: str) -> str` con soporte Unicode completo.

## Archivos a modificar

### [MODIFY] main.py
- Agregar `from utils import slugify` al tope del archivo (línea ~19, después de los imports locales)
- Eliminar bloque inline líneas 162-166 (import re + def slugify + el return)
- Eliminar bloque inline líneas 304-307 (segunda definición)
- Eliminar bloque inline líneas 1184-1187 (tercera definición)
- Verificar que las 3 referencias a `slugify(...)` siguen funcionando

## Decisión de implementación: slugify con Unicode

La versión actual ignora caracteres especiales del español. La nueva versión los normaliza:
```python
import unicodedata, re

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
```
Esto es retrocompatible — el output para texto ASCII es idéntico a la versión anterior.

