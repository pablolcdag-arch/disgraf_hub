import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, Form, Request, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
import secrets
import requests
from google import genai
from datetime import datetime
import asyncio
from seo_service import run_seo_workflow
from utils import slugify


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Setup

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configurar directorio de datos
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory mock DB for sessions (cookie based for UI simplicity)
sessions = {}

# Users Mock DB
USERS = {
    os.getenv("ADMIN_USERNAME", "pablo"): {"password": os.getenv("ADMIN_PASSWORD", "admin"), "role": "admin"},
    os.getenv("SELLER_USERNAME", "ventas"): {"password": os.getenv("SELLER_PASSWORD", "ventas"), "role": "seller"},
}

def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        return None
    return sessions[session_token]

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        if user["role"] == "seller":
            return RedirectResponse(url="/cotizador", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = USERS.get(username)
    if not user or user["password"] != password:
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Credenciales inválidas"})
    
    # Create session
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {"username": username, "role": user["role"]}
    
    target_url = "/cotizador" if user["role"] == "seller" else "/dashboard"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@app.get("/marketing", response_class=HTMLResponse)
async def marketing_page(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="marketing.html", context={"user": user})

@app.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token in sessions:
        del sessions[session_token]
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    if user["role"] == "seller":
        return RedirectResponse(url="/cotizador", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user})

@app.get("/precios", response_class=HTMLResponse)
async def precios_page(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="precios.html", context={"user": user})

@app.get("/cotizador", response_class=HTMLResponse)
async def cotizador_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="cotizador.html", context={"user": user})

@app.get("/clientes", response_class=HTMLResponse)
async def clientes_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="clientes.html", context={"user": user})

@app.get("/media", response_class=HTMLResponse)
async def media_page(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="media.html", context={"user": user})

@app.get("/marketing", response_class=HTMLResponse)
async def marketing_page(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="marketing.html", context={"user": user})

@app.get("/satellite-demo", response_class=HTMLResponse)
async def satellite_demo_page(request: Request):
    return templates.TemplateResponse(request=request, name="satellite_demo.html")

@app.get("/v2", response_class=HTMLResponse)
async def storefront_v2(request: Request):
    catalog = get_v2_catalog_data()
    return templates.TemplateResponse(request=request, name="v2_home.html", context={"catalog": catalog})

@app.get("/v2/categoria/{slug}", response_class=HTMLResponse)
async def storefront_v2_category(request: Request, slug: str):
    catalog = get_v2_catalog_data()
    category = next((c for c in catalog if slugify(c["name"]) == slug), None)
    if not category:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/v2")
        
    return templates.TemplateResponse(request=request, name="v2_category.html", context={
        "catalog": catalog, 
        "category": category,
        "slug": slug
    })

def get_blog_posts():
    import json, os
    blog_path = os.path.join(DATA_DIR, 'blog_posts.json')
    if not os.path.exists(blog_path):
        return []
    try:
        with open(blog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# Blog is now Headless. Public routes removed to avoid duplicate content SEO penalty.

ORACAL_COLORS = {
    "000": "transparent", "010": "#FFFFFF", "020": "#FCAE1E", "019": "#F3B200", 
    "021": "#F9C00D", "022": "#F5C24D", "025": "#FFE066", "026": "#960018",
    "030": "#8A0303", "031": "#C8102E", "032": "#DA291C", "034": "#E84E0F",
    "036": "#E1523D", "035": "#F36F21", "040": "#4D148C", "043": "#7566A0",
    "041": "#D12267", "045": "#F089B6", "042": "#B87F9B", "050": "#00205B",
    "051": "#003DA5", "052": "#0055A4", "053": "#0072CE", "057": "#1E90FF",
    "056": "#5CB8E6", "066": "#005A8C", "054": "#00A19A", "055": "#71C5E8",
    "060": "#006747", "061": "#007A53", "062": "#00965E", "064": "#43B02A",
    "063": "#84C225", "080": "#3D2415", "083": "#8C6954", "081": "#AD8B73",
    "082": "#E8D3C3", "070": "#000000", "073": "#4C4E52", "071": "#7C878E",
    "072": "#A5ACAF", "074": "#9EA2A2", "076": "#B7BFC7", "090": "#A2AAAD",
    "091": "#D4AF37", "092": "#CD7F32", "312": "#6D0020", "404": "#5E2D79",
    "562": "#003A70", "518": "#4A90E2", "613": "#00A859",
    # Fallback for 2-digit format
    "00": "transparent", "10": "#FFFFFF", "20": "#FCAE1E", "19": "#F3B200",
    "21": "#F9C00D", "22": "#F5C24D", "25": "#FFE066", "26": "#960018",
    "30": "#8A0303", "31": "#C8102E", "32": "#DA291C", "34": "#E84E0F",
    "36": "#E1523D", "35": "#F36F21", "40": "#4D148C", "43": "#7566A0",
    "41": "#D12267", "45": "#F089B6", "42": "#B87F9B", "50": "#00205B",
    "51": "#003DA5", "52": "#0055A4", "53": "#0072CE", "57": "#1E90FF",
    "56": "#5CB8E6", "66": "#005A8C", "54": "#00A19A", "55": "#71C5E8",
    "60": "#006747", "61": "#007A53", "62": "#00965E", "64": "#43B02A",
    "63": "#84C225", "80": "#3D2415", "83": "#8C6954", "81": "#AD8B73",
    "82": "#E8D3C3", "70": "#000000", "73": "#4C4E52", "71": "#7C878E",
    "72": "#A5ACAF", "74": "#9EA2A2", "76": "#B7BFC7", "90": "#A2AAAD",
    "91": "#D4AF37", "92": "#CD7F32"
}

def get_v2_catalog_data():
    import os, json, io
    import pandas as pd
    
    maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
    selected_path = os.path.join(DATA_DIR, 'productos_seleccionados.csv')
    
    if not os.path.exists(maestro_path) or not os.path.exists(selected_path):
        return []
        
    try:
        df_saas = pd.read_csv(maestro_path, sep=';', encoding='utf-8', on_bad_lines='skip')
    except:
        df_saas = pd.read_csv(maestro_path, sep=';', encoding='latin-1', on_bad_lines='skip')
        
    df_saas.columns = df_saas.columns.str.strip()
    col_id = 'Nº de producto'
    col_desc = 'Nombre'
    col_price = 'Precio ($)'
    col_unit = 'Unidad'
    if col_id not in df_saas.columns: col_id = df_saas.columns[0]
    
    product_map = {}
    for index, row in df_saas.iterrows():
        p_id = str(row.get(col_id, '')).strip()
        p_name = str(row.get(col_desc, '')).strip()
        p_unit = str(row.get(col_unit, '')).strip()
        try:
            p_price = float(str(row.get(col_price, 0)).replace(',', '.'))
        except:
            p_price = 0
            
        if p_id and p_price > 0:
            import re
            color_hex = None
            has_color_chart = False
            
            if "ORACAL" in p_name.upper() or "ORALITE" in p_name.upper() or "651" in p_name:
                match = re.search(r'-(\d{2,3})\b', p_name)
                if match:
                    code = match.group(1).zfill(3)
                    color_hex = ORACAL_COLORS.get(code)
                    if not color_hex:
                        color_hex = ORACAL_COLORS.get(match.group(1))
            
            if "(Brillante y Mate)" in p_name or "Colores" in p_name or "Blanco y Negro" in p_name:
                has_color_chart = True

            product_map[p_id] = {"id": p_id, "name": p_name, "price": p_price, "unit": p_unit, "color_hex": color_hex, "has_color_chart": has_color_chart}
            
    catalog = []
    current_cat_obj = None
    current_sub_obj = None
    
    with open(selected_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('codigo_producto') or line.startswith('Los precios'):
                continue
                
            parts = line.split(',')
            codigo = parts[0].strip()
            if not codigo: continue
            
            if codigo.startswith('@@SUB@@'):
                sub_name = codigo.replace('@@SUB@@', '').strip()
                current_sub_obj = {"name": sub_name, "products": []}
                if current_cat_obj:
                    current_cat_obj["subcategories"].append(current_sub_obj)
            elif not codigo.isdigit() and not codigo.startswith('@@SUB@@'):
                current_cat_obj = {"name": codigo, "subcategories": []}
                catalog.append(current_cat_obj)
                current_sub_obj = None
            else:
                if codigo in product_map:
                    if current_sub_obj:
                        current_sub_obj["products"].append(product_map[codigo])
                    elif current_cat_obj:
                        if not current_cat_obj["subcategories"]:
                            current_cat_obj["subcategories"].append({"name": "General", "products": []})
                        current_cat_obj["subcategories"][0]["products"].append(product_map[codigo])
                        
    valid_catalog = []
    for cat in catalog:
        cat["subcategories"] = [sub for sub in cat["subcategories"] if len(sub["products"]) > 0]
        if len(cat["subcategories"]) > 0:
            cat["slug"] = slugify(cat["name"])
            valid_catalog.append(cat)
            
    return valid_catalog

@app.get("/api/v2/products")
async def api_v2_products():
    return get_v2_catalog_data()

@app.get("/sitemap.xml")
async def sitemap_xml():
    from fastapi.responses import Response
    catalog = get_v2_catalog_data()
    
    base_url = "https://hub.disgraf.com.ar"
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Home V2
    xml_content += '  <url>\n'
    xml_content += f'    <loc>{base_url}/v2</loc>\n'
    xml_content += '    <changefreq>daily</changefreq>\n'
    xml_content += '    <priority>1.0</priority>\n'
    xml_content += '  </url>\n'
    
    # Categories
    for cat in catalog:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{base_url}/v2/categoria/{cat["slug"]}</loc>\n'
        xml_content += '    <changefreq>weekly</changefreq>\n'
        xml_content += '    <priority>0.8</priority>\n'
        xml_content += '  </url>\n'
        
    xml_content += '</urlset>'
    
    return Response(content=xml_content, media_type="application/xml")

@app.post("/api/upload-saas")
async def api_upload_saas(request: Request, saas_file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
    
    import pandas as pd
    import io
    import os
    
    try:
        content_saas = await saas_file.read()
        
        # Save as maestro with backup
        maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
        backup_path = os.path.join(DATA_DIR, 'maestro_productos_backup.csv')
        import shutil
        if os.path.exists(maestro_path):
            shutil.copy2(maestro_path, backup_path)
            
        with open(maestro_path, 'wb') as f:
            f.write(content_saas)
            
        try:
            df_saas = pd.read_csv(io.BytesIO(content_saas), sep=';', encoding='utf-8', on_bad_lines='skip')
        except:
            df_saas = pd.read_csv(io.BytesIO(content_saas), sep=';', encoding='latin-1', on_bad_lines='skip')
            
        df_saas.columns = df_saas.columns.str.strip()
        
        # Extract all products
        saas_products = []
        col_id = 'Nº de producto' # The actual ID column in the CSV
        col_desc = 'Nombre'
        col_cat = 'Rubro'
        col_price = 'Precio ($)'
        col_unit = 'Unidad'
        
        # If columns have strange names due to encoding, fallback to index
        if col_id not in df_saas.columns:
            col_id = df_saas.columns[0]
            
        for index, row in df_saas.iterrows():
            p_id = str(row.get(col_id, '')).strip()
            p_name = str(row.get(col_desc, '')).strip()
            p_cat = str(row.get(col_cat, '')).strip()
            p_price = str(row.get(col_price, '')).strip()
            p_unit = str(row.get(col_unit, '')).strip()
            
            if p_id and p_name:
                saas_products.append({
                    "id": p_id,
                    "name": p_name,
                    "category": p_cat,
                    "price": p_price,
                    "unit": p_unit
                })
                
        # Read current selected catalog
        selected_path = os.path.join(DATA_DIR, 'productos_seleccionados.csv')
        selected_catalog = []
        
        if os.path.exists(selected_path):
            with open(selected_path, 'r', encoding='utf-8') as f:
                current_category = ""
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('codigo_producto') or line.startswith('Los precios'):
                        continue
                        
                    parts = line.split(',')
                    codigo = parts[0].strip()
                    unidad = parts[1].strip() if len(parts) > 1 else ""
                    
                    if not codigo:
                        continue
                    
                    if codigo.startswith('@@SUB@@'):
                        selected_catalog.append({
                            "id": codigo,
                            "catalog_category": current_category
                        })
                    elif not codigo.isdigit() and not codigo.startswith('@@SUB@@'):
                        current_category = codigo
                    else:
                        selected_catalog.append({
                            "id": codigo,
                            "catalog_category": current_category
                        })
                        
        import json
        meta_path = os.path.join(DATA_DIR, 'categorias_meta.json')
        category_meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    category_meta = json.load(f)
            except:
                pass
                        
        return {"saas_products": saas_products, "selected_catalog": selected_catalog, "category_meta": category_meta}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/load-catalog")
async def api_load_catalog(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import pandas as pd
    import os
    
    saas_products = []
    maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
    
    if os.path.exists(maestro_path):
        try:
            df_saas = pd.read_csv(maestro_path, sep=';', encoding='utf-8', on_bad_lines='skip')
        except:
            df_saas = pd.read_csv(maestro_path, sep=';', encoding='latin-1', on_bad_lines='skip')
            
        df_saas.columns = df_saas.columns.str.strip()
        
        col_id = 'Nº de producto'
        col_desc = 'Nombre'
        col_cat = 'Rubro'
        col_price = 'Precio ($)'
        col_unit = 'Unidad'
        
        if col_id not in df_saas.columns:
            col_id = df_saas.columns[0]
            
        for index, row in df_saas.iterrows():
            p_id = str(row.get(col_id, '')).strip()
            p_name = str(row.get(col_desc, '')).strip()
            p_cat = str(row.get(col_cat, '')).strip()
            p_price = str(row.get(col_price, '')).strip()
            p_unit = str(row.get(col_unit, '')).strip()
            
            if p_id and p_name:
                saas_products.append({
                    "id": p_id,
                    "name": p_name,
                    "category": p_cat,
                    "price": p_price,
                    "unit": p_unit
                })
                
    selected_path = os.path.join(DATA_DIR, 'productos_seleccionados.csv')
    selected_catalog = []
    
    if os.path.exists(selected_path):
        with open(selected_path, 'r', encoding='utf-8') as f:
            current_category = ""
            for line in f:
                line = line.strip()
                if not line or line.startswith('codigo_producto') or line.startswith('Los precios'):
                    continue
                    
                parts = line.split(',')
                codigo = parts[0].strip()
                
                if not codigo:
                    continue
                
                if codigo.startswith('@@SUB@@'):
                    selected_catalog.append({
                        "id": codigo,
                        "catalog_category": current_category
                    })
                elif not codigo.isdigit() and not codigo.startswith('@@SUB@@'):
                    current_category = codigo
                else:
                    selected_catalog.append({
                        "id": codigo,
                        "catalog_category": current_category
                    })
                    
    import json
    meta_path = os.path.join(DATA_DIR, 'categorias_meta.json')
    category_meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                category_meta = json.load(f)
        except:
            pass
                
    return {"saas_products": saas_products, "selected_catalog": selected_catalog, "category_meta": category_meta}

@app.post("/api/restore-backup")
async def api_restore_backup(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    import os
    import shutil
    maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
    backup_path = os.path.join(DATA_DIR, 'maestro_productos_backup.csv')
    
    if not os.path.exists(backup_path):
        return {"error": "No hay ningún backup disponible para restaurar."}
        
    try:
        shutil.copy2(backup_path, maestro_path)
        return {"status": "success", "message": "Respaldo restaurado con éxito."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/save-catalog")
async def api_save_catalog(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    catalog_data = data.get("catalog", {}) # dict of { "Category Name": ["id1", "id2"] }
    category_meta = data.get("categoryMeta", {})
    
    import os
    import json
    selected_path = os.path.join(DATA_DIR, 'productos_seleccionados.csv')
    meta_path = os.path.join(DATA_DIR, 'categorias_meta.json')
    
    try:
        # Save Metadata
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(category_meta, f, ensure_ascii=False, indent=4)
            
        # Save Catalog
        with open(selected_path, 'w', encoding='utf-8') as f:
            f.write("codigo_producto,unidad_medida\n")
            f.write("Los precios no incluyen IVA,\n")
            for cat, ids in catalog_data.items():
                f.write(f"{cat},\n")
                for pid in ids:
                    f.write(f"{pid},\n")
                f.write(",\n") # Empty line separator
                
        return {"status": "success", "message": "Catálogo guardado correctamente"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/run-legacy-sync")
async def api_run_legacy_sync(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    import subprocess
    import os
    
    script_dir = "/Users/pablostiefel/Documents/Lista de precios aut Disgraf"
    script_path = os.path.join(script_dir, "wp_sync.py")
    
    try:
        # Ejecutar el script externo usando python3
        result = subprocess.run(
            ["python3", script_path], 
            cwd=script_dir,
            capture_output=True, 
            text=True,
            check=True
        )
        return {"status": "success", "message": "Sincronización completada exitosamente.", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e.stderr}")
        return {"error": f"Error ejecutando el script: {e.stderr}"}
    except Exception as e:
        print(f"Exception: {str(e)}")
        return {"error": str(e)}

@app.post("/api/sync-wordpress")
async def api_sync_wordpress(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    catalog_data = data.get("catalog", {})
    saas_products = {p["id"]: p for p in data.get("saasProducts", [])}
    category_meta = data.get("categoryMeta", {})
    
    import urllib.request
    import urllib.parse
    import base64
    import json
    
    WP_URL = os.getenv("WP_URL", "https://disgraf.com.ar/wp-json/wp/v2/pages")
    USERNAME = os.getenv("WP_USER", "c1502162")
    PASSWORD = os.getenv("WP_APP_PASSWORD", "P0z0 VBTV rHYX QXjD pFRz qRui")
    
    auth = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("utf-8")).decode("utf-8")
    
    def hacer_peticion_wp(method, url, payload=None):
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Basic {auth}")
        req.add_header("User-Agent", "Mozilla/5.0")
        
        if payload:
            req.add_header("Content-Type", "application/json")
            req.data = json.dumps(payload).encode("utf-8")
            
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"WP Request Error: {e}")
            return None
            
    def buscar_pagina(titulo):
        query = urllib.parse.urlencode({"search": titulo, "status": "any"})
        url = f"{WP_URL}?{query}"
        res = hacer_peticion_wp("GET", url)
        if res and isinstance(res, list) and len(res) > 0:
            for page in res:
                # Decodificamos el título devuelto por si WP escapa caracteres
                page_title = page.get("title", {}).get("rendered", "").replace("&#8211;", "-").strip()
                if page_title == titulo:
                    return page["id"]
        return None

    def format_price(p):
        if not str(p).strip(): return ""
        try:
            clean_str = str(p).replace('$', '').strip().replace('.', '').replace(',', '.')
            num = float(clean_str)
            return f"$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(p)
            
    # WhatsApp Config (Replace with real number)
    WA_NUMBER = os.getenv("WA_NUMBER", "5491100000000")

    try:
        results = []
        for cat, item_ids in catalog_data.items():
            if not item_ids:
                continue
                
            meta = category_meta.get(cat, {})
            
            html = f"<h2>Catálogo de {cat}</h2>"
            
            # 1. SEO Text
            seo_text = meta.get("seo_text")
            if seo_text:
                html += f"<p style='font-size: 1.1em; color: #475569;'><strong>{seo_text}</strong></p>"
                
            # 2. Logos Fila
            logos = meta.get("logos", [])
            if logos:
                html += "<div style='display: flex; gap: 20px; align-items: center; margin: 20px 0;'>"
                for logo_url in logos:
                    html += f"<img src='{logo_url}' alt='Logo marca' style='max-height: 60px; object-fit: contain;'>"
                html += "</div>"
                
            # 3. WhatsApp CTA Banner (Lead Generation) - Only if enabled
            show_cta = meta.get("show_cta", False)
            if show_cta:
                cta_text = meta.get("cta_whatsapp") or "Solicitá la carta de colores digital y consultá disponibilidad de stock por WhatsApp."
                wa_link = f"https://wa.me/{WA_NUMBER}?text=Hola,%20quisiera%20pedir%20la%20carta%20de%20colores%20y%20consultar%20stock%20de%20{urllib.parse.quote(cat)}"
                
                html += f'''
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 25px; margin: 25px 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 20px;">
                    <div style="flex: 1 1 250px; text-align: left;">
                        <h3 style="margin: 0 0 8px 0; color: #166534; font-size: 1.25em;">🎨 ¿Necesitás ver los colores?</h3>
                        <p style="margin: 0; color: #15803d; line-height: 1.4; font-size: 1.05em;">{cta_text}</p>
                    </div>
                    <div style="flex: 0 1 auto; text-align: center; width: auto; margin: auto;">
                        <a href="{wa_link}" target="_blank" style="background-color: #22c55e; color: white; padding: 14px 28px; border-radius: 50px; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 6px -1px rgba(34,197,94,0.3); font-size: 1.05em; line-height: 1; mso-line-height-rule: exactly;">
                            <span style="display: flex; align-items: center;">💬</span>
                            <span style="display: flex; align-items: center;">Pedir Carta</span>
                        </a>
                    </div>
                </div>
                '''
                
            # 4. Pricing Table
            html += "<table border='1' cellpadding='10' style='width:100%; border-collapse: collapse; border-color: #e2e8f0; margin-top: 30px;'>"
            html += f"<tr style='background-color:#f1f5f9;'><th style='text-align:left'>Producto</th><th style='text-align:center'>Unidad</th><th style='text-align:right'>Precio (+ IVA)</th></tr>"

            
            for pid in item_ids:
                if pid.startswith('@@SUB@@'):
                    sub_text = pid.replace('@@SUB@@', '')
                    html += f"<tr><td colspan='3' style='background-color: #f8fafc; font-weight: bold; text-align: center; color: #334155; padding: 12px;'>{sub_text}</td></tr>"
                    continue
                    
                p_info = saas_products.get(pid, {})
                desc = p_info.get("name", "Producto Desconocido").capitalize()
                price = format_price(p_info.get("price", ""))
                unit = p_info.get("unit", "")
                if unit == "nan": unit = ""
                
                html += f"<tr><td>{desc}</td><td style='text-align:center'>{unit}</td><td style='text-align:right'><strong>{price}</strong></td></tr>"
            
            html += "</table>"
            
            # Enviar a WP como BORRADOR
            wp_data = {
                "title": cat,
                "content": html,
                "status": "draft"
            }
            
            page_id = buscar_pagina(cat)
            action = "created"
            if page_id:
                hacer_peticion_wp("POST", f"{WP_URL}/{page_id}", wp_data)
                action = "updated"
            else:
                hacer_peticion_wp("POST", WP_URL, wp_data)
                
            results.append({"category": cat, "action": action})
            
        return {"status": "success", "results": results}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/log-quote")
async def api_log_quote(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    data = await request.json()
    client_name = data.get("client_name", "Consumidor Final")
    if not client_name.strip():
        client_name = "Consumidor Final"
        
    total = data.get("total", 0)
    products = data.get("products", [])
    
    # Construir mensaje para Telegram
    lines = [
        f"🚨 <b>Nuevo Presupuesto Generado</b>",
        f"👤 <b>Vendedor:</b> {user['username']}",
        f"🏢 <b>Cliente:</b> {client_name}",
        f"💰 <b>Total:</b> ${total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        "",
        "📦 <b>Productos:</b>"
    ]
    
    for p in products:
        lines.append(f"• {p['name']} {p['unit']} - {p['quantity']}x = ${p['subtotal']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
    msg = "\n".join(lines)
    
    # Aquí iría el envío real a Telegram.
    # Por ahora lo imprimimos en consola y lo dejamos preparado.
    print("=== ENVIANDO A TELEGRAM ===")
    print(msg)
    print("===========================")
    
    # Para habilitarlo de verdad en DonWeb:
    # import requests
    # TOKEN = 'tu_token_aqui'
    # CHAT_ID = 'tu_chat_id_aqui'
    # try:
    #     requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
    # except Exception as e:
    #     print("Error Telegram:", e)
        
    # --- Guardar Historial ---
    import os
    import json
    import datetime
    
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    history_data = []
    
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except:
            pass
            
    # Añadir nuevo registro
    import uuid
    new_record = {
        "id": str(uuid.uuid4())[:8],
        "date": datetime.datetime.now().isoformat(),
        "seller": user["username"],
        "client": client_name,
        "client_id": data.get("client_id"),
        "total": total,
        "products": products,
        "tipoB": data.get("tipoB", False)
    }
    history_data.insert(0, new_record) # Insert at beginning
    
    # Limpiar antiguos (>10 días)
    ten_days_ago = datetime.datetime.now() - datetime.timedelta(days=10)
    valid_history = []
    for r in history_data:
        try:
            r_date = datetime.datetime.fromisoformat(r["date"])
            if r_date >= ten_days_ago:
                valid_history.append(r)
        except:
            pass
            
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(valid_history, f, ensure_ascii=False, indent=2)
        
    return {"status": "success"}

@app.get("/api/history-quotes")
async def api_history_quotes(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import os
    import json
    
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

@app.delete("/api/history-quotes/{quote_id}")
async def api_delete_history_quote(quote_id: str, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    import os
    import json
    
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if not os.path.exists(history_path):
        return {"error": "History file not found"}
        
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        new_history = [q for q in history if q.get("id") != quote_id]
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/clientes/buscar")
async def api_buscar_clientes(q: str = "", limit: int = 10, request: Request = None):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import sqlite3
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    if not os.path.exists(db_path):
        return []
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f"%{q}%"
        cursor.execute('''
            SELECT id, nombre, contacto, condicion_iva, cuit 
            FROM clientes 
            WHERE nombre LIKE ? OR cuit LIKE ? OR razon_social LIKE ?
            LIMIT ?
        ''', (query, query, query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print("Error buscando clientes:", e)
        return []

@app.get("/api/clientes/{client_id}")
async def api_get_cliente(client_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import sqlite3
    db_path = os.path.join(DATA_DIR, 'disgraf_hub.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return {"error": "Cliente no encontrado"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/clientes/{client_id}/presupuestos")
async def api_get_cliente_presupuestos(client_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    import json
    history_path = os.path.join(DATA_DIR, 'historial_presupuestos.json')
    if not os.path.exists(history_path):
        return []
        
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        client_history = [q for q in history if str(q.get("client_id")) == str(client_id)]
        return client_history
    except:
        return []

@app.post("/api/media/upload")
async def api_media_upload(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    media_dir = os.path.join(DATA_DIR, "media")
    os.makedirs(media_dir, exist_ok=True)
    
    file_path = os.path.join(media_dir, file.filename)
    with open(file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "success", "filename": file.filename}

@app.get("/api/media/list")
async def api_media_list(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return {"error": "Unauthorized"}
        
    media_dir = os.path.join(DATA_DIR, "media")
    os.makedirs(media_dir, exist_ok=True)
    
    files = []
    for f in os.listdir(media_dir):
        if os.path.isfile(os.path.join(media_dir, f)):
            files.append({"filename": f, "url": f"/media/file/{f}"})
            
    return files

@app.get("/media/file/{filename}")
async def media_serve_file(filename: str):
    media_dir = os.path.join(DATA_DIR, "media")
    file_path = os.path.join(media_dir, filename)
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.get("/api/marketing/config")
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
            "youtube": [],
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

@app.post("/api/marketing/config")
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

@app.post("/api/marketing/generate-article")
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
            sources = config.get("websites", []) + config.get("youtube", [])
    
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
                channel_instruction = "Eres un maestro del Car Wrapping y ploteo vehicular. Tu enfoque es explicar cómo usar herramientas de calor, espátulas de fieltro y las ventajas de usar la serie Oracal 970 o Orajet 3951. Habla sobre la maleabilidad, adhesivos canalizados (RapidAir) y terminaciones premium. Menciona explícitamente a Orafol, Avery y Arlon."
            elif channel == "instagram_disgraf":
                channel_instruction = "Eres el Community Manager de Disgraf. Escribe un caption corto, vibrante y vendedor para Instagram, usando emojis. Enfocate en la urgencia y en que somos distribuidores oficiales de Orafol. Menciona productos estrella como Oracal 651 o Poli-Tape. No uses formato HTML, solo texto puro con hashtags."
            else:
                channel_instruction = "Eres un experto aplicador gráfico de oficio. Habla sobre cartelería, vinilos de corte e impresión de gran formato. SI el tema provisto está relacionado explícitamente con vinilos, destaca sutilmente productos específicos de Orafol como Oracal 651 para corte, o Orajet 3164 y 3651 para impresión. Si el tema NO está relacionado con vinilos (por ejemplo, es sobre Lonas, Herramientas, etc), NO menciones productos de Orafol ni los fuerces en el texto."

            context_text = f"Contexto extraído de la fuente ({source}):\n{scraped_text}\n\n" if scraped_text else f"Tema de inspiración: {source}\n\n"
            catalog_text = get_catalog_summary(DATA_DIR)

            prompt = f"{channel_instruction}\n\n{context_text}{catalog_text}Escribe un artículo/post útil e interesante basado en esto. Traduce cualquier información técnica al español argentino de forma natural. El contenido debe ser profundo y práctico: no te limites a explicar qué es un producto, incluye siempre consejos de aplicación, técnicas (ej. cómo tensar un cartel, qué pegamento usar para doblez), diferencias con materiales similares (ej. front vs backlite) y buenas prácticas de taller para aportar valor real al lector.\n\nSalvo que sea para Instagram, el artículo debe tener un título llamativo (con etiqueta h1 o ##), estar formateado en HTML (solo contenido interno, usar h2, h3, p) y tener un tono profesional.\n\nHacia el final del artículo, debes hacer una referencia MUY SUTIL a Disgraf usando este texto o algo muy similar: 'En Argentina, podés conseguir todos los materiales e insumos para tu taller de cartelería e impresión de gran formato a través de www.disgraf.com.ar'. IMPORTANTE: Respeta las REGLAS DE VENTA del catálogo para saber cuándo puedes mencionar venta fraccionada."

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

@app.get("/api/marketing/drafts")
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

@app.delete("/api/marketing/drafts/{post_id}")
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

@app.put("/api/marketing/drafts/{post_id}")
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

@app.post("/api/marketing/drafts/{post_id}/approve")
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
            
        for p in posts:
            if p.get("id") == post_id:
                p["status"] = "published"
                
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4)
            
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/marketing/drafts/{post_id}/image")
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

@app.get("/api/marketing/drafts/{post_id}/preview", response_class=HTMLResponse)
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
            
            html = f"<html><body style='font-family:sans-serif; max-width:800px; margin:0 auto; padding:20px;'>"
            html += f"<div style='background:#f1f5f9; padding:10px; margin-bottom:20px;'><strong>Canal:</strong> {post.get('channel')} | <strong>Estado:</strong> {post.get('status')}</div>"
            if post.get('image_url'):
                html += f"<img src='{post.get('image_url')}' style='width:100%; border-radius:12px; margin-bottom:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);' alt='Portada del Artículo'>"
            html += f"<h1>{post.get('title')}</h1>"
            html += f"<div>{post.get('content')}</div>"
            html += "</body></html>"
            return html
    except Exception as e:
        return str(e)

@app.get("/api/public/content/{channel}")
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
        return published
    except:
        return []

@app.get("/api/sync/woocommerce")
async def api_sync_woocommerce(request: Request):
    """
    Endpoint público/protegido para que WordPress (WP All Import o cron) 
    consuma el catálogo completo y lo sincronice.
    """
    import json
    saas_path = os.path.join(DATA_DIR, 'productos_saas.json')
    if not os.path.exists(saas_path):
        return {"error": "Catálogo no disponible."}
        
    try:
        with open(saas_path, 'r', encoding='utf-8') as f:
            productos = json.load(f)
            
        # Transform or clean data if needed for WooCommerce
        sync_payload = []
        for p in productos:
            sync_payload.append({
                "sku": p.get("codigo", ""),
                "name": p.get("nombre", ""),
                "price": p.get("precio", 0),
                "stock": p.get("stock", 0),
                "category": p.get("rubro", "General"),
                "status": "publish"
            })
            
        return {"status": "success", "count": len(sync_payload), "products": sync_payload}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/generate-quote-pdf")
async def api_generate_quote_pdf(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "Unauthorized"}
        
    data = await request.json()
    client_name = data.get("client_name", "Consumidor Final")
    if not client_name.strip():
        client_name = "Consumidor Final"
        
    products = data.get("products", [])
    total = data.get("total", 0)
    tipo_b = data.get("tipoB", False)
    global_discount = data.get("globalDiscount", 0)
    
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from fastapi.responses import Response
    import io
    import datetime
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#1e293b'),
        alignment=0,
        spaceAfter=10
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        spaceAfter=5
    )
    
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    )
    
    # Cabecera
    elements.append(Paragraph("<b>PRESUPUESTO DISGRAF</b>", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Fecha:</b> {datetime.datetime.now().strftime('%d/%m/%Y')}", info_style))
    elements.append(Paragraph(f"<b>Cliente:</b> {client_name}", info_style))
    elements.append(Paragraph(f"<b>Vendedor:</b> {user['username'].capitalize()}", info_style))
    elements.append(Spacer(1, 25))
    
    # Tabla de productos
    table_data = [["Descripción", "Unidad", "Precio Unit.", "Desc.", "Cant.", "Subtotal"]]
    
    for p in products:
        desc_para = Paragraph(p['name'], cell_style)
        price_str = f"$ {p['price']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        subtotal_str = f"$ {p['subtotal']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        discount_str = f"{p.get('discount', 0)}%" if p.get('discount', 0) > 0 else "-"
        
        table_data.append([
            desc_para, 
            p['unit'], 
            price_str,
            discount_str,
            str(p['quantity']), 
            subtotal_str
        ])
        
    t = Table(table_data, colWidths=[180, 60, 80, 40, 40, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea5e9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (2,0), (5,-1), 'RIGHT'),
        ('ALIGN', (3,0), (4,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,1), (-1,-1), 8),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Total y Descuento Global
    if global_discount > 0:
        elements.append(Paragraph(f"<b>Descuento especial aplicado: {global_discount}%</b>", info_style))
        elements.append(Spacer(1, 10))
    
    total_str = f"$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#1e293b'),
        alignment=2 # Right align
    )
    
    if tipo_b:
        elements.append(Paragraph(f"<b>Total (Final): {total_str}</b>", total_style))
    else:
        elements.append(Paragraph(f"<b>Total Estimado (+ IVA 21%): {total_str}</b>", total_style))
        
        iva_amount = total * 0.21
        total_with_iva = total * 1.21
        
        iva_str = f"$ {iva_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        total_with_iva_str = f"$ {total_with_iva:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        sub_style = ParagraphStyle(
            'SubTotal',
            parent=styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#ef4444'),
            alignment=2
        )
        
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"iva {iva_str}", sub_style))
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(f"total: {total_with_iva_str}", sub_style))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Presupuesto_Disgraf.pdf"})

@app.post("/api/generate-pdf")
async def api_generate_pdf(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    data = await request.json()
    catalog_data = data.get("catalog", {})
    saas_products = {p["id"]: p for p in data.get("saasProducts", [])}
    
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from fastapi.responses import Response
    import io
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0ea5e9'),
        alignment=1,
        spaceAfter=20
    )
    
    cat_style = ParagraphStyle(
        'Category',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        backColor=colors.HexColor('#1e293b'),
        alignment=0,
        spaceBefore=15,
        spaceAfter=5,
        leftIndent=10,
        rightIndent=10
    )
    
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )
    
    # Title
    elements.append(Paragraph("Catálogo Disgraf", title_style))
    
    # Format Currency (Argentine format: 1.234,56)
    def format_price(p):
        if not str(p).strip(): return ""
        try:
            clean_str = str(p).replace('$', '').strip().replace('.', '').replace(',', '.')
            num = float(clean_str)
            return f"$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(p)
            
    # Draw Categories
    for cat, item_ids in catalog_data.items():
        if not item_ids:
            continue
            
        elements.append(Paragraph(f"<b>{cat}</b>", cat_style))
        elements.append(Spacer(1, 10))
        
        data = [["Código", "Descripción", "Unidad", "Precio (+ IVA)"]]
        sub_row_indices = []
        
        for pid in item_ids:
            if pid.startswith('@@SUB@@'):
                sub_text = pid.replace('@@SUB@@', '')
                data.append(["", sub_text, "", ""])
                sub_row_indices.append(len(data) - 1)
                continue
                
            p_info = saas_products.get(pid, {})
            desc_text = p_info.get("name", "Producto Desconocido").capitalize()
            desc_para = Paragraph(desc_text, cell_style)
            price = format_price(p_info.get("price", ""))
            unit = p_info.get("unit", "")
            if unit == "nan": unit = ""
            data.append([pid, desc_para, unit, price])
            
        t = Table(data, colWidths=[50, 310, 60, 100])
        base_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,0), 'LEFT'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('ALIGN', (2,0), (2,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]
        
        for idx in sub_row_indices:
            base_style.extend([
                ('SPAN', (1, idx), (-1, idx)),
                ('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#f8fafc')),
                ('FONTNAME', (1, idx), (-1, idx), 'Helvetica-Bold'),
                ('ALIGN', (1, idx), (-1, idx), 'LEFT'),
                ('TEXTCOLOR', (1, idx), (-1, idx), colors.HexColor('#334155'))
            ])
            
        t.setStyle(TableStyle(base_style))
        elements.append(t)
        elements.append(Spacer(1, 15))
        
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=Catalogo_Disgraf.pdf"
        }
    )

@app.post("/api/generate-seo")
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

@app.post("/api/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" not in data or "text" not in data["message"]:
        return {"status": "ok"}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    def process_message():
        if not GEMINI_API_KEY:
            reply = "No tengo cerebro conectado (Falta GEMINI_API_KEY)."
        else:
            try:
                import json
                
                quotes_file = os.path.join(DATA_DIR, 'historial_presupuestos.json')
                history = []
                if os.path.exists(quotes_file):
                    with open(quotes_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                
                from datetime import datetime, timedelta
                
                today = datetime.now()
                today_date = today.strftime("%Y-%m-%d")
                today_quotes = [q for q in history if q.get("date", "").startswith(today_date)]
                
                # Filter history for the last 15 days
                fifteen_days_ago = today - timedelta(days=15)
                recent_quotes = []
                for q in history:
                    q_date_str = q.get("date", "")
                    if q_date_str:
                        try:
                            # Handle ISO format dates
                            q_date = datetime.fromisoformat(q_date_str)
                            if q_date >= fifteen_days_ago:
                                recent_quotes.append(q)
                        except:
                            pass
                
                total_today = sum(q.get("total", 0) for q in today_quotes)
                total_b = sum(1 for q in today_quotes if q.get("tipoB"))
                total_a = len(today_quotes) - total_b
                
                summary = f"Hoy ({today_date}) se hicieron {len(today_quotes)} presupuestos. "
                summary += f"Total presupuestado estimado: ${total_today:,.2f}. "
                summary += f"Presupuestos Tipo B: {total_b}. Presupuestos Normales: {total_a}."
                
                prompt = f"""Eres el Asistente Inteligente de la plataforma Disgraf Hub. 
El usuario que te habla es tu jefe (Pablo) o un administrador de ventas. Responde sus consultas basándote estrictamente en los datos proporcionados.
Si te pide presupuestos, analiza los datos. No inventes respuestas. Responde siempre en un tono amable pero directo, sin excederte en saludos.

REGLAS DE FORMATO (MUY IMPORTANTE):
Telegram NO soporta tablas Markdown (como | Cliente | Total |). NUNCA uses tablas.
1. SIEMPRE comienza tu respuesta con un resumen del día consultado. Ejemplo: "Aquí tienes los presupuestos registrados el día [Fecha]: se realizaron X presupuestos por un total de $X."
2. Si tienes que listar presupuestos o datos, usa listas limpias con emojis y negritas. Ejemplo de cómo debes listar:

👤 **Nombre Cliente** (Vendedor)
🔹 Producto principal resumido...
💰 Total: $1,234.00
📝 ID: 1234abcd

NUEVO COMANDO (SÚPER IMPORTANTE):
Si el usuario te pide explícitamente "crear una oferta", "hacer un blog", "crear una promo" de algún producto específico, DEBES responder exactamente con este formato:
[ACCION_SEO: Nombre del Producto]

Por ejemplo, si dice "Haceme una promo del Vinilo Esmerilado", respondes:
[ACCION_SEO: Vinilo Esmerilado]
(Y nada más, solo esa línea).

Resumen del día de hoy:
{summary}

Historial COMPLETO de presupuestos de los últimos 15 días (en formato JSON):
{json.dumps(recent_quotes, ensure_ascii=False)}

La pregunta del usuario es: {text}
"""
                response = gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                reply = response.text.strip()
                
                # Check if it is an SEO action
                if reply.startswith("[ACCION_SEO:") and reply.endswith("]"):
                    product_target = reply.replace("[ACCION_SEO:", "").replace("]", "").strip()
                    reply = f"🚀 Entendido. Generando un post de blog y oferta SEO para: *{product_target}*. Esto tardará unos segundos, publicando..."
                    
                    # Send immediate response
                    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": reply,
                        "parse_mode": "Markdown"
                    })
                    
                    # Run SEO in background
                    try:
                        link = run_seo_workflow(product_target)
                        msg = f"✅ ¡Post publicado exitosamente en el blog!\n\n🔗 Puedes verlo aquí: {link}"
                    except Exception as e:
                        msg = f"❌ Ocurrió un error al intentar publicar el artículo: {str(e)}"
                        
                    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "Markdown"
                    })
                    return # Exit early for SEO actions
                    
            except Exception as e:
                reply = f"Error procesando con IA: {str(e)}"

        if TELEGRAM_TOKEN:
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown"
            })
            
        # --- Guardar Log de Conversacion (10 días) ---
        try:
            chat_log_file = os.path.join(DATA_DIR, 'telegram_chat_history.json')
            chat_history = []
            if os.path.exists(chat_log_file):
                with open(chat_log_file, 'r', encoding='utf-8') as f:
                    chat_history = json.load(f)
                    
            now = datetime.now()
            chat_history.append({
                "timestamp": now.isoformat(),
                "user_text": text,
                "bot_reply": reply
            })
            
            ten_days_ago = now - __import__('datetime').timedelta(days=10)
            valid_chat_history = []
            for msg in chat_history:
                try:
                    msg_date = datetime.fromisoformat(msg["timestamp"])
                    if msg_date >= ten_days_ago:
                        valid_chat_history.append(msg)
                except:
                    pass
                    
            with open(chat_log_file, 'w', encoding='utf-8') as f:
                json.dump(valid_chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error guardando log de telegram:", e)
            
    import threading
    threading.Thread(target=process_message).start()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
