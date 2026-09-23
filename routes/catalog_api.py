from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import Response
from dependencies import get_current_user, DATA_DIR
import os
import json
import pandas as pd
import io
import shutil
import subprocess
import urllib.request
import urllib.parse
import base64
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter()
@router.get("/api/export-maestro")
async def api_export_maestro(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return {"error": "Unauthorized"}
        
    from fastapi.responses import FileResponse
    import os
    
    maestro_path = os.path.join(DATA_DIR, 'maestro_productos.csv')
    if not os.path.exists(maestro_path):
        return {"error": "El archivo maestro no existe aún. Por favor suba un CSV primero."}
        
    return FileResponse(
        path=maestro_path, 
        filename="maestro_productos_exportado.csv", 
        media_type="text/csv"
    )

@router.post("/api/upload-saas")
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
            
        # Detect encoding and delimiter
        try:
            first_line = content_saas.split(b'\n')[0].decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            first_line = content_saas.split(b'\n')[0].decode('latin-1')
            encoding = 'latin-1'
            
        delimiter = ';' if first_line.count(';') >= first_line.count(',') else ','
        
        try:
            df_saas = pd.read_csv(io.BytesIO(content_saas), sep=delimiter, encoding=encoding, on_bad_lines='skip')
        except:
            df_saas = pd.read_csv(io.BytesIO(content_saas), sep=delimiter, encoding=encoding, on_bad_lines='skip', engine='python')
            
        df_saas.columns = df_saas.columns.str.strip()
        
        if 'Nº de producto' not in df_saas.columns or 'Nombre' not in df_saas.columns:
            return {"error": "No se encontraron las columnas esperadas (Nº de producto, Nombre). Verifique el formato del CSV."}
        
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

@router.get("/api/load-catalog")
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

@router.post("/api/restore-backup")
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

@router.post("/api/save-catalog")
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

@router.post("/api/run-legacy-sync")
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

@router.post("/api/sync-wordpress")
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

@router.get("/api/sync/woocommerce")
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

@router.post("/api/generate-pdf")
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

