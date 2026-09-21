import os
import re
import datetime
from google import genai
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from utils import slugify

load_dotenv()

BLOG_OUTPUT_DIR = os.getenv("BLOG_OUTPUT_DIR", os.path.join(os.getcwd(), "data", "blog_output"))

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

def render_and_save_post(title, content):
    slug = slugify(title)
    date_str = datetime.datetime.now().strftime("%d %b, %Y")
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("v2_blog_post.html")
    
    post_data = {
        "title": title,
        "content": content,
        "date": date_str,
        "slug": slug
    }
    
    html_output = template.render(post=post_data)
    
    os.makedirs(BLOG_OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(BLOG_OUTPUT_DIR, f"{slug}.html")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    return file_path

def run_seo_workflow(product_name):
    html_content = generate_blog_post(product_name)

    match = re.search(r'<h1>(.*?)</h1>', html_content, re.IGNORECASE)
    title = match.group(1) if match else f"Guía sobre {product_name}"

    content_clean = re.sub(r'<h1>.*?</h1>', '', html_content, flags=re.IGNORECASE).strip()

    file_path = render_and_save_post(title, content_clean)
    return file_path
