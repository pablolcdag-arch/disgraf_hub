"""
Migración: agregar columnas faltantes a la tabla `comprobantes`.

Columnas objetivo:
  - comprobante_asociado_id  INTEGER DEFAULT NULL
  - numero_afip              INTEGER DEFAULT NULL
  - cae                      TEXT    DEFAULT NULL
  - cae_vto                  TEXT    DEFAULT NULL

Este script es idempotente: no falla si las columnas ya existen.
Ejecutar desde la raíz del proyecto:
    python3 migrate_comprobante_asociado.py
"""

import sqlite3
import os

db_path = os.path.join(os.environ.get("DATA_DIR", "./data"), "disgraf_hub.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

existing = [row[1] for row in cursor.execute("PRAGMA table_info(comprobantes)")]
print("Columnas existentes:", existing)

columns_to_add = [
    ("comprobante_asociado_id", "INTEGER DEFAULT NULL"),
    ("numero_afip", "INTEGER DEFAULT NULL"),
    ("cae", "TEXT DEFAULT NULL"),
    ("cae_vto", "TEXT DEFAULT NULL"),
]

for col_name, col_def in columns_to_add:
    if col_name not in existing:
        cursor.execute(f"ALTER TABLE comprobantes ADD COLUMN {col_name} {col_def}")
        print(f"  ✅ Agregada columna: {col_name}")
    else:
        print(f"  ⏭  Ya existe: {col_name}")

conn.commit()
conn.close()
print("\nMigración completada.")
