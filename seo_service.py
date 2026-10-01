import os
import re
import logging
import datetime
import json
from google import genai
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from utils import slugify

load_dotenv()

# Configurar logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BLOG_OUTPUT_DIR = os.getenv("BLOG_OUTPUT_DIR", os.path.join(os.getcwd(), "data", "blog_output"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def generate_blog_post(product_name):
    if not gemini_client:
        logger.error("Falta GEMINI_API_KEY")
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

Genera SOLO código HTML válido (usando h2, p, ul, li, strong) que no dependa de estilos externos. 
No envuelvas la respuesta en ```html, solo devuelve el contenido puro HTML listo para usar.
"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text.replace("```html", "").replace("```", "").strip()
    except Exception as e:
        logger.error(f"Error al generar contenido con Gemini API: {str(e)}")
        raise Exception(f"Error en Gemini API: {str(e)}")

def render_and_save_post(title, content, slug=None, date_str=None, post_dict=None):
    slug = slug or slugify(title)
    date_str = date_str or datetime.datetime.now().strftime("%d %b, %Y")
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("v2_blog_post.html")
    
    content_parsed = re.sub(
        r'\[FOTO:\s*(.*?)\]', 
        r'<img src="/media/file/\1" style="max-width:350px; width:100%; height:auto; display:block; margin:20px auto; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);" alt="Imagen ilustrativa del artículo">', 
        content
    )
    
    if post_dict:
        post_data = dict(post_dict)
        post_data["content"] = content_parsed
    else:
        post_data = {
            "title": title,
            "content": content_parsed,
            "date": date_str,
            "slug": slug
        }
    
    html_output = template.render(post=post_data)
    
    try:
        os.makedirs(BLOG_OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(BLOG_OUTPUT_DIR, f"{slug}.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_output)
            
        logger.info(f"Post generado exitosamente en: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error al guardar el archivo HTML: {str(e)}")
        raise Exception(f"Error al guardar HTML: {str(e)}")

def run_seo_workflow(product_name):
    try:
        html_content = generate_blog_post(product_name)

        match = re.search(r'<h1>(.*?)</h1>', html_content, re.IGNORECASE)
        title = match.group(1) if match else f"Guía sobre {product_name}"

        content_clean = re.sub(r'<h1>.*?</h1>', '', html_content, flags=re.IGNORECASE).strip()

        file_path = render_and_save_post(title, content_clean)
        return file_path
    except Exception as e:
        logger.error(f"Error en el workflow SEO para '{product_name}': {str(e)}")
        raise

def rebuild_static_site():
    """Genera todo el sitio estático basándose en los posts publicados."""
    db_path = os.path.join(os.getcwd(), 'data', 'marketing_content.json')
    if not os.path.exists(db_path):
        logger.warning("No hay base de datos de marketing para reconstruir.")
        return

    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except Exception as e:
        logger.error(f"Error al leer marketing_content.json: {e}")
        return
        
    published_posts = [p for p in posts if p.get("status") == "published"]
    
    # Sort by published_date descending
    published_posts.sort(
        key=lambda x: x.get("published_date", x.get("date", "")), 
        reverse=True
    )
    
    # 1. Generate individual HTML for each post
    for post in published_posts:
        title = post.get("title", "Sin Título")
        content = post.get("content", "")
        slug = post.get("slug", slugify(title))
        render_and_save_post(title, content, slug=slug, post_dict=post)

    # 2. Render index.html
    env = Environment(loader=FileSystemLoader("templates"))
    try:
        template = env.get_template("oficio_index.html")
        html_output = template.render(posts=published_posts)
        
        os.makedirs(BLOG_OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(BLOG_OUTPUT_DIR, "index.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_output)
            
        logger.info(f"Sitio estático reconstruido. index.html guardado en: {file_path}")
    except Exception as e:
        logger.error(f"Error al renderizar el index estático: {e}")

