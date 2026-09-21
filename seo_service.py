import os
import requests
from google import genai
import re
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def generate_blog_post(product_name):
    if not gemini_client:
        raise Exception("Falta GEMINI_API_KEY")

    prompt = f"""Eres un experto en marketing digital y experto aplicador gráfico (cartelería, vinilos de corte, impresión, etc).
Escribe un artículo de blog altamente optimizado para SEO para la empresa "Disgraf" en Argentina.

El artículo debe enfocarse en este producto o temática: "{product_name}".

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
    if not WP_URL or not WP_USER or not WP_APP_PASSWORD:
        raise Exception("Faltan credenciales de WordPress")

    api_url = f"{WP_URL}/wp-json/wp/v2/posts"
    credentials = (WP_USER, WP_APP_PASSWORD)

    post_data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }

    response = requests.post(api_url, auth=credentials, json=post_data)

    if response.status_code == 201:
        data = response.json()
        return data.get("link", "")
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def run_seo_workflow(product_name):
    html_content = generate_blog_post(product_name)

    match = re.search(r'<h1>(.*?)</h1>', html_content, re.IGNORECASE)
    title = match.group(1) if match else f"Guía sobre {product_name}"

    content_clean = re.sub(r'<h1>.*?</h1>', '', html_content, flags=re.IGNORECASE).strip()

    link = post_to_wordpress(title, content_clean)
    return link
