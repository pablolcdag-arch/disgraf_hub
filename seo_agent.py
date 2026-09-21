import os
import csv
import random
import datetime
from dotenv import load_dotenv

# Importar el servicio unificado
from seo_service import run_seo_workflow

# Configurar entorno
load_dotenv(dotenv_path="/opt/disgraf_hub/.env")
# Fallback a local (.env) si no hay variables cargadas
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "/opt/disgraf_hub/data")
# Fallback local para desarrollo si /opt no existe
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(os.getcwd(), "data")

CATALOG_PATH = os.path.join(DATA_DIR, "maestro_productos.csv")

def select_random_product():
    if not os.path.exists(CATALOG_PATH):
        return None
        
    products = []
    with open(CATALOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
        for row in reader:
            if len(row) > 1 and row[1].strip():
                products.append(row[1].strip())
    if not products:
        return None
    return random.choice(products)

def main():
    print(f"Iniciando Agente SEO - {datetime.datetime.now()}")

    product_name = select_random_product()
    if not product_name:
        print(f"Error: No se encontraron productos en el catálogo ({CATALOG_PATH}).")
        return

    print(f"Producto seleccionado: {product_name}")
    print(f"Generando y publicando artículo (SSG)...")
    
    try:
        file_path = run_seo_workflow(product_name)
        print(f"Éxito: El post se generó correctamente en {file_path}")
    except Exception as e:
        print(f"Error al generar el post: {e}")

if __name__ == "__main__":
    main()
