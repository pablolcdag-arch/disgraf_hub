from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from dependencies import templates, DATA_DIR
from utils import slugify
import os
import json
import pandas as pd
import re
import random

router = APIRouter()

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
    maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
    selected_path = os.path.join(DATA_DIR, 'productos_seleccionados.csv')
    
    if not os.path.exists(maestro_path) or not os.path.exists(selected_path):
        return []
        
    try:
        df_saas = pd.read_csv(maestro_path, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
    except:
        df_saas = pd.read_csv(maestro_path, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        
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

@router.get("/v2", response_class=HTMLResponse)
async def storefront_v2(request: Request):
    catalog = get_v2_catalog_data()
    return templates.TemplateResponse(request=request, name="v2_home.html", context={"catalog": catalog})

@router.get("/v2/buscar", response_class=HTMLResponse)
async def storefront_v2_search(request: Request, q: str = Query("")):
    catalog = get_v2_catalog_data()
    results = []
    
    q_lower = q.lower().strip()
    if q_lower:
        for cat in catalog:
            for sub in cat.get("subcategories", []):
                for prod in sub.get("products", []):
                    if q_lower in prod["name"].lower() or q_lower in prod["id"].lower():
                        # Evitar duplicados si el producto aparece en múltiples subcategorías
                        if not any(p["id"] == prod["id"] for p in results):
                            # Añadimos la categoría original para tener referencia si se necesita
                            prod_with_cat = dict(prod)
                            prod_with_cat["category_name"] = cat["name"]
                            results.append(prod_with_cat)
                            
    return templates.TemplateResponse(request=request, name="v2_search.html", context={
        "catalog": catalog,
        "q": q,
        "results": results
    })

@router.get("/v2/categoria/{slug}", response_class=HTMLResponse)
async def storefront_v2_category(request: Request, slug: str):
    catalog = get_v2_catalog_data()
    category = next((c for c in catalog if slugify(c["name"]) == slug), None)
    if not category:
        return RedirectResponse(url="/v2")
        
    return templates.TemplateResponse(request=request, name="v2_category.html", context={
        "catalog": catalog, 
        "category": category,
        "slug": slug
    })

@router.get("/v2/producto/{product_id}", response_class=HTMLResponse)
async def storefront_v2_product(request: Request, product_id: str):
    catalog = get_v2_catalog_data()
    
    target_product = None
    target_category = None
    target_subcategory = None
    
    for cat in catalog:
        for sub in cat.get("subcategories", []):
            for prod in sub.get("products", []):
                if prod["id"] == product_id:
                    target_product = prod
                    target_category = cat
                    target_subcategory = sub
                    break
            if target_product:
                break
        if target_product:
            break
            
    if not target_product:
        return templates.TemplateResponse(
            request=request, 
            name="v2_404.html", 
            context={"catalog": catalog}, 
            status_code=404
        )
        
    related_products = []
    if target_category:
        try:
            meta_path = os.path.join(DATA_DIR, 'categorias_meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                # Intentar primero con el slug de la subcategoría
                sub_slug = slugify(target_subcategory["name"]) if target_subcategory else ""
                cat_slug = slugify(target_category["name"])
                
                related_slugs = []
                if sub_slug in meta_data and "relacionados" in meta_data[sub_slug]:
                    related_slugs = meta_data[sub_slug]["relacionados"]
                elif cat_slug in meta_data and "relacionados" in meta_data[cat_slug]:
                    related_slugs = meta_data[cat_slug]["relacionados"]
                    
                if related_slugs:
                    potential_products = []
                    
                    for cat in catalog:
                        # Add products if category slug matches
                        if cat.get("name") and slugify(cat["name"]) in related_slugs:
                            for sub in cat.get("subcategories", []):
                                potential_products.extend(sub.get("products", []))
                        # Also add products if subcategory slug matches
                        else:
                            for sub in cat.get("subcategories", []):
                                if slugify(sub.get("name", "")) in related_slugs:
                                    potential_products.extend(sub.get("products", []))
                                
                    if potential_products:
                        sample_size = min(4, len(potential_products))
                        related_products = random.sample(potential_products, sample_size)
        except Exception:
            pass
            
    # Fallback: Si no hay productos relacionados por metadata, sugerir de la misma categoría
    if not related_products and target_category:
        potential_products = []
        for sub in target_category.get("subcategories", []):
            for prod in sub.get("products", []):
                if prod["id"] != product_id:
                    potential_products.append(prod)
        if potential_products:
            sample_size = min(4, len(potential_products))
            related_products = random.sample(potential_products, sample_size)
            
    return templates.TemplateResponse(request=request, name="v2_product.html", context={
        "catalog": catalog,
        "category": target_category,
        "product": target_product,
        "related_products": related_products
    })

@router.get("/api/v2/products")
async def api_v2_products():
    return get_v2_catalog_data()

@router.get("/sitemap.xml")
async def sitemap_xml():
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

