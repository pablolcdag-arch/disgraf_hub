import os
import csv
import random
import requests
import datetime
from google import genai
from dotenv import load_dotenv

# Configurar entorno
load_dotenv(dotenv_path="/opt/disgraf_hub/.env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

if not GEMINI_API_KEY or not WP_URL or not WP_USER or not WP_APP_PASSWORD:
    print("Error: Faltan variables de entorno necesarias.")
    exit(1)

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

DATA_DIR = "/opt/disgraf_hub/data"
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

def generate_blog_post(product_name):
    prompt = f"""Eres un experto en marketing digital y experto aplicador gráfico (cartelería, vinilos de corte, impresión, etc).
Escribe un artículo de blog altamente optimizado para SEO para la empresa "Disgraf" en Argentina.

El artículo debe enfocarse en este producto: "{product_name}".

El objetivo del blog es educar al cliente y posicionar nuestra marca en Google.
Incluye:
1. Un título atractivo y llamativo (HTML <h1>).
2. Introducción que despierte interés.
3. Técnicas o consejos útiles para aplicar este material sobre diferentes superficies o usos comunes.
4. Un llamado a la acción (Call to Action) invitando a comprarlo en Disgraf.

Genera SOLO código HTML válido (usando h2, p, ul, li, strong) que pueda ser insertado directamente en el editor de WordPress. 
No envuelvas la respuesta en ```html, solo devuelve el contenido puro HTML listo para usar.
"""
    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text.replace("```html", "").replace("```", "").strip()

def post_to_wordpress(title, content):
    api_url = f"{WP_URL}/wp-json/wp/v2/posts"
    credentials = (WP_USER, WP_APP_PASSWORD)

    post_data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }

    response = requests.post(api_url, auth=credentials, json=post_data)

    if response.status_code == 201:
        print(f"Éxito: El post '{title}' se publicó correctamente.")
    else:
        print(f"Error al crear el post: {response.status_code}")
        print(response.text)

def main():
    print(f"Iniciando Agente SEO - {datetime.datetime.now()}")

    product_name = select_random_product()
    if not product_name:
        print("Error: No se encontraron productos en el catálogo.")
        return

    print(f"Producto seleccionado: {product_name}")

    html_content = generate_blog_post(product_name)

    import re
    match = re.search(r'<h1>(.*?)</h1>', html_content, re.IGNORECASE)
    title = match.group(1) if match else f"Guía sobre {product_name}"

    content_clean = re.sub(r'<h1>.*?</h1>', '', html_content, flags=re.IGNORECASE).strip()

    print(f"Publicando artículo: {title}")
    post_to_wordpress(title, content_clean)

if __name__ == "__main__":
    main()
