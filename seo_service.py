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
REGLAS ESTRICTAS DE FORMATO HTML:
1. NO generar etiqueta H1 (ya la pone el template Jinja). Para sugerir el título, ponlo al principio como '## Título del Artículo'.
2. Introducción atrapante aplicando la técnica de la pirámide invertida.
3. Uso estricto de jerarquía <H2> y <H3>.
4. Inclusión obligatoria de listas (<ul><li>) para romper la monotonía visual. Incluye técnicas o consejos útiles para aplicar el material.
5. Un <H2> final llamado "Conclusión".
6. Un llamado a la acción (Call to Action) claro al final invitando a visitar nuestro catálogo en https://hub.disgraf.com.ar/v2 (usa un enlace HTML real).

Genera SOLO código HTML válido (solo contenido interno, sin html/body) que no dependa de estilos externos. 
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

def render_and_save_post(title, content, slug=None, date_str=None, post_dict=None, categories=None):
    slug = slug or slugify(title)
    date_str = date_str or datetime.datetime.now().strftime("%d %b, %Y")
    categories = categories or []
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("oficio_post.html")
    
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
    
    html_output = template.render(post=post_data, categories=categories)
    
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

        match = re.search(r'## (.*?)\n', html_content)
        title = match.group(1).replace("*", "").strip() if match else f"Guía sobre {product_name}"

        content_clean = re.sub(r'## (.*?)\n', '', html_content, count=1).strip()

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
    
    unique_categories = {}
    for p in published_posts:
        cat_name = p.get("category", "Sin Categoría")
        cat_slug = slugify(cat_name)
        if cat_slug not in unique_categories:
            unique_categories[cat_slug] = {"name": cat_name, "slug": cat_slug}
            
    categories = list(unique_categories.values())
    
    # 1. Generate individual HTML for each post
    for post in published_posts:
        title = post.get("title", "Sin Título")
        content = post.get("content", "")
        slug = post.get("slug", slugify(title))
        render_and_save_post(title, content, slug=slug, post_dict=post, categories=categories)

    # 2. Render index.html
    env = Environment(loader=FileSystemLoader("templates"))
    try:
        template = env.get_template("oficio_index.html")
        html_output = template.render(posts=published_posts, categories=categories)
        
        os.makedirs(BLOG_OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(BLOG_OUTPUT_DIR, "index.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_output)
            
        logger.info(f"Sitio estático reconstruido. index.html guardado en: {file_path}")
        
        # 3. Render and save static pages
        static_pages = [
            ("oficio_about.html", "about.html"),
            ("oficio_contact.html", "contacto.html"),
            ("oficio_legal.html", "legales.html")
        ]
        
        for tpl_name, out_name in static_pages:
            try:
                page_tpl = env.get_template(tpl_name)
                page_html = page_tpl.render(categories=categories)
                page_out_path = os.path.join(BLOG_OUTPUT_DIR, out_name)
                with open(page_out_path, "w", encoding="utf-8") as f:
                    f.write(page_html)
                logger.info(f"Página estática generada: {out_name}")
            except Exception as e:
                logger.error(f"Error al renderizar {tpl_name}: {e}")
                
        # 4. Generar páginas de categorías
        cat_dir = os.path.join(BLOG_OUTPUT_DIR, "categoria")
        os.makedirs(cat_dir, exist_ok=True)
        for cat in categories:
            cat_posts = [p for p in published_posts if slugify(p.get("category", "Sin Categoría")) == cat["slug"]]
            cat_html = template.render(posts=cat_posts, categories=categories, current_category=cat)
            cat_file_path = os.path.join(cat_dir, f"{cat['slug']}.html")
            with open(cat_file_path, "w", encoding="utf-8") as f:
                f.write(cat_html)
            logger.info(f"Página de categoría generada: {cat['slug']}.html")
            
        # 5. Generate sitemap.xml
        sitemap_urls = []
        base_url = "https://oficiocarteleria.com.ar"
        
        # Home
        sitemap_urls.append(base_url + "/")
        
        # Static pages
        for _, out_name in static_pages:
            sitemap_urls.append(f"{base_url}/{out_name}")
            
        # Categories
        for cat in categories:
            sitemap_urls.append(f"{base_url}/categoria/{cat['slug']}.html")
            
        # Posts
        for post in published_posts:
            sitemap_urls.append(f"{base_url}/{post.get('slug')}.html")
            
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for url in sitemap_urls:
            sitemap_content += f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
        sitemap_content += '</urlset>'
        
        sitemap_path = os.path.join(BLOG_OUTPUT_DIR, "sitemap.xml")
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(sitemap_content)
        logger.info(f"sitemap.xml generado en: {sitemap_path}")

    except Exception as e:
        logger.error(f"Error al renderizar el index estático o páginas estáticas: {e}")

