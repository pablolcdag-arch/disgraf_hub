from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from dependencies import get_current_user, DATA_DIR, gemini_client
import os
import json
import datetime
import re
import random
import requests
import shutil
import asyncio
from bs4 import BeautifulSoup
from seo_service import run_seo_workflow
from utils import slugify

router = APIRouter()
@router.get("/api/marketing/config")
async def api_get_marketing_config(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    config_path = os.path.join(DATA_DIR, 'marketing_config.json')
    if os.path.exists(config_path):
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # Default config
    return {
        "satellites": [],
        "frequency": 2,
        "sources": {
            "websites": []
        }
    }

def get_catalog_summary(data_dir):
    import csv
    csv_path = os.path.join(data_dir, 'maestro_productos.csv')
    if not os.path.exists(csv_path): return ""
    product_units = {}
    try:
        with open(csv_path, encoding='iso-8859-1') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)
            for row in reader:
                if len(row) > 14:
                    rubro = row[6].strip()
                    unidad = row[14].strip().lower()
                    if rubro and rubro != "Sin especificar":
                        if rubro not in product_units:
                            product_units[rubro] = set()
                        product_units[rubro].add(unidad)
        
        summary = "REGLAS DE VENTA (CATÁLOGO OFICIAL DE DISGRAF):\n"
        for r, u in product_units.items():
            u_list = list(u)
            if 'metro' in u_list and 'unidad' in u_list:
                rule = "Se vende por rollo cerrado o fraccionado por metro."
            elif 'metro' in u_list:
                rule = "Se vende fraccionado por metro."
            else:
                rule = "Se vende SÓLO por unidad (rollo cerrado). PROHIBIDO mencionar venta fraccionada para este producto."
            summary += f"- {r}: {rule}\n"
        return summary + "\nUTILIZA ESTAS REGLAS para saber si puedes mencionar 'venta fraccionada por metro' o si debes decir 'venta por rollo cerrado' al recomendar productos.\n\n"
    except Exception as e:
        print(f"Error leyendo catalogo: {e}")
        return ""

@router.post("/api/marketing/config")
async def api_save_marketing_config(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    config_path = os.path.join(DATA_DIR, 'marketing_config.json')
    
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    return {"status": "success"}

@router.post("/api/marketing/generate-article")
async def api_generate_article(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    import json, os, datetime, re
    import random
    import requests
    from bs4 import BeautifulSoup
    
    data = await request.json()
    channel = data.get("channel", "oficio_carteleria")
    
    config_path = os.path.join(DATA_DIR, 'marketing_config.json')
    sources = []
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            sources = config.get("websites", [])
    
    specific_source = data.get("specific_source")
    custom_topic = data.get("custom_topic", "").strip()
    
    if custom_topic:
        source = custom_topic
    elif specific_source:
        source = specific_source
    else:
        source = random.choice(sources) if sources else "Conocimiento General de Insumos Gráficos"
    
    # Scrape content if source is a URL
    scraped_text = ""
    if source.startswith("http"):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(source, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Extract main paragraphs
                paragraphs = soup.find_all('p')
                scraped_text = " ".join([p.get_text() for p in paragraphs])
                scraped_text = scraped_text[:3000] # Limit to 3000 chars to avoid prompt overflow
        except Exception as e:
            print(f"Error scraping {source}: {e}")

    content = ""
    title = ""
    try:
        if gemini_client:
            # Channel specific instructions
            channel_instruction = ""
            if channel == "car_wrapping":
                channel_instruction = "Eres un maestro del Car Wrapping y ploteo vehicular. Tu enfoque es explicar cómo usar herramientas de calor, espátulas de fieltro y técnicas avanzadas. Habla sobre maleabilidad, adhesivos canalizados y terminaciones premium. Mantén una postura neutral y experta, mencionando marcas variadas como Avery, Orafol, Arlon o 3M según corresponda, sin sesgo comercial."
            elif channel == "instagram_disgraf":
                channel_instruction = "Eres el Community Manager de Disgraf. Escribe un caption corto, vibrante y vendedor para Instagram, usando emojis. Enfócate en la urgencia y nuestro amplio catálogo multimarca. Menciona productos variados sin preferencia. No uses formato HTML, solo texto puro con hashtags."
            else:
                channel_instruction = "Eres un experto aplicador gráfico de oficio. Habla sobre cartelería, vinilos de corte e impresión de gran formato. Mantén una postura 100% neutral y experta: si el tema es lona, habla solo de lona. Si es impresión, menciona marcas variadas de la industria (como DPI, Avery, Orafol, Arlon) sin favorecer a ninguna en particular. Tu objetivo es aportar valor educativo, sin sesgos comerciales forzados."

            context_text = f"Contexto extraído de la fuente ({source}):\n{scraped_text}\n\n" if scraped_text else f"Tema de inspiración: {source}\n\n"
            catalog_text = get_catalog_summary(DATA_DIR)

            prompt = f"{channel_instruction}\n\n{context_text}{catalog_text}Escribe un artículo/post útil e interesante basado en esto. Traduce cualquier información técnica al español argentino de forma natural. El contenido debe ser profundo y práctico: no te limites a explicar qué es un producto, incluye siempre consejos de aplicación, técnicas (ej. cómo tensar un cartel, qué pegamento usar para doblez), diferencias con materiales similares (ej. front vs backlite) y buenas prácticas de taller para aportar valor real al lector.\n\nSalvo que sea para Instagram, el artículo debe tener un título llamativo (con etiqueta h1 o ##), estar formateado en HTML (solo contenido interno, usar h2, h3, p) y tener un tono profesional.\n\nHacia el final del artículo, debes hacer una referencia MUY SUTIL a Disgraf. DEBES incluir obligatoriamente un enlace HTML real apuntando a https://disgraf.com.ar. Por ejemplo: '<a href=\"https://disgraf.com.ar\">www.disgraf.com.ar</a>'. No dejes el enlace como texto plano. IMPORTANTE: Respeta las REGLAS DE VENTA del catálogo para saber cuándo puedes mencionar venta fraccionada."

            response = gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            raw_text = response.text
            
            # Extract title and remove it from content to prevent duplication
            title_match = re.search(r'<h1>(.*?)</h1>', raw_text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).replace("*", "").strip()
                raw_text = re.sub(r'<h1>.*?</h1>', '', raw_text, flags=re.IGNORECASE, count=1).strip()
            else:
                title_match = re.search(r'## (.*?)\n', raw_text)
                if title_match:
                    title = title_match.group(1).replace("*", "").strip()
                    raw_text = re.sub(r'## (.*?)\n', '', raw_text, count=1).strip()
                else:
                    title = "Novedades y Consejos para tu Gráfica"
            
            content = raw_text.replace("```html", "").replace("```", "").strip()
            
            # Los shortcodes ahora se mantienen crudos en la base de datos
            # y se parsean únicamente al renderizar (previsualización o generación estática).
            
    except Exception as e:
        print(f"Error AI: {e}")
        pass
        
    if not content:
        title = f"Guía Rápida: {source}"
        content = "<p>Error al generar el artículo mediante IA.</p>"

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    slug = f"{slugify(title)}-{datetime.datetime.now().strftime('%H%M%S')}"
    
    new_post = {
        "id": f"draft_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": title,
        "slug": slug,
        "date": date_str,
        "content": content,
        "source": source,
        "channel": channel,
        "status": "draft"
    }
    
    # Save to marketing_content.json instead of blog_posts.json
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    posts = []
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        except:
            pass
            
    posts.insert(0, new_post) # Insert at beginning
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)
        
    return {"status": "success", "post": new_post}

@router.get("/api/marketing/drafts")
async def api_get_marketing_drafts(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return []
    
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            return posts
    except:
        return []

@router.delete("/api/marketing/drafts/{post_id}")
async def api_delete_draft(request: Request, post_id: str):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return {"error": "No database"}
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            
        posts = [p for p in posts if p.get("id") != post_id]
                
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4)
            
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@router.put("/api/marketing/drafts/{post_id}")
async def api_update_draft(request: Request, post_id: str):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    new_title = data.get("title")
    new_content = data.get("content")
    
    if not new_title or not new_content:
        return {"error": "Title and content are required"}
        
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return {"error": "No database"}
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            
        updated = False
        for p in posts:
            if p.get("id") == post_id:
                p["title"] = new_title
                p["content"] = new_content
                updated = True
                break
                
        if not updated:
            return {"error": "Post not found"}
                
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4)
            
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/marketing/drafts/{post_id}/approve")
async def api_approve_draft(request: Request, post_id: str):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return {"error": "No database"}
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            
        import datetime
        for p in posts:
            if p.get("id") == post_id:
                p["status"] = "published"
                p["published_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4)
            
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/api/marketing/drafts/{post_id}/image")
async def api_upload_draft_image(request: Request, post_id: str, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    import json, os, shutil
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return {"error": "No hay borradores"}
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            
        post_found = False
        for p in posts:
            if p.get("id") == post_id:
                post_found = True
                
                # Ensure uploads directory exists
                upload_dir = os.path.join("static", "uploads", "marketing")
                os.makedirs(upload_dir, exist_ok=True)
                
                # Create safe filename
                ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
                filename = f"{post_id}.{ext}"
                file_path = os.path.join(upload_dir, filename)
                
                # Save file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                p["image_url"] = f"/static/uploads/marketing/{filename}"
                break
                
        if not post_found:
            return {"error": "Borrador no encontrado"}
            
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4)
            
        return {"status": "success", "image_url": f"/static/uploads/marketing/{filename}"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/marketing/drafts/{post_id}/preview", response_class=HTMLResponse)
async def api_preview_draft(request: Request, post_id: str):
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return "Not found"
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            post = next((p for p in posts if p.get("id") == post_id), None)
            if not post:
                return "Not found"
            
            import re
            content_parsed = re.sub(
                r'\[FOTO:\s*(.*?)\]', 
                r'<img src="/media/file/\1" style="max-width:200px; width:100%; height:auto; display:block; margin:20px auto; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);" alt="Imagen ilustrativa del artículo">', 
                post.get('content', '')
            )
            
            html = f"<html><body style='font-family:sans-serif; background-color: #f1f5f9; margin:0; padding:20px;'>"
            html += f"<div style='max-width:800px; margin:0 auto; padding:40px; background-color:#ffffff; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.05);'>"
            html += f"<div style='background:#f8fafc; padding:12px 15px; margin-bottom:30px; border-radius:8px; font-size:14px; border:1px solid #e2e8f0;'><strong>Canal:</strong> {post.get('channel')} | <strong>Estado:</strong> {post.get('status')}</div>"
            if post.get('image_url'):
                html += f"<img src='{post.get('image_url')}' style='width:100%; max-height:400px; object-fit:cover; border-radius:12px; margin-bottom:30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);' alt='Portada del Artículo'>"
            html += f"<h1 style='margin-bottom:30px; line-height:1.2;'>{post.get('title')}</h1>"
            html += f"<div style='font-size:18px; line-height:1.8; color:#333;'>{content_parsed}</div>"
            html += "</div></body></html>"
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)
    except Exception as e:
        return str(e)

@router.get("/api/public/content/{channel}")
async def api_public_content(request: Request, channel: str):
    """ Headless CMS Endpoint for satellite domains """
    import json, os
    db_path = os.path.join(DATA_DIR, 'marketing_content.json')
    if not os.path.exists(db_path):
        return []
        
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
            
        # Filter by channel and status published
        published = [p for p in posts if p.get("status") == "published" and p.get("channel") == channel]
        import re
        for p in published:
            p["content"] = re.sub(
                r'\[FOTO:\s*(.*?)\]', 
                r'<img src="/media/file/\1" style="max-width:350px; width:100%; height:auto; display:block; margin:20px auto; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);" alt="Imagen ilustrativa del artículo">', 
                p.get('content', '')
            )
        return published
    except:
        return []
@router.post("/api/generate-seo")
async def api_generate_seo(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    product_name = data.get("product_name")
    
    if not product_name:
        return {"error": "Falta product_name"}
        
    try:
        # Run synchronous function in thread pool
        link = await asyncio.to_thread(run_seo_workflow, product_name)
        return {"status": "ok", "link": link}
    except Exception as e:
        return {"error": str(e)}
