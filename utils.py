"""
utils.py — Funciones utilitarias compartidas de Disgraf Hub
Todas las funciones de este módulo son puras (sin side effects).
Importar desde aquí, nunca redefinir inline en otros módulos.
"""

import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convierte un texto en un slug URL-friendly.
    Soporta caracteres Unicode (á, é, ñ, ü, etc.) normalizándolos a ASCII.

    Ejemplos:
        slugify("Vinilos de Corte")  → "vinilos-de-corte"
        slugify("ORACAL 651 (Brillante)")  → "oracal-651-brillante"
        slugify("Señalética & Herrajes")  → "senaletica-herrajes"
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

