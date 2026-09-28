import json
import sys
import os
sys.path.append(".")
from utils import slugify
from routes.v2 import get_v2_catalog_data

catalog = get_v2_catalog_data()
target_category = None

for cat in catalog:
    for sub in cat.get("subcategories", []):
        for prod in sub.get("products", []):
            if str(prod.get("id")) == "1373":
                target_category = cat
                break

cat_slug = slugify(target_category.get("name", ""))
print("SLUG DE LA CATEGORIA:", cat_slug)

with open("data/categorias_meta.json", "r") as f:
    meta_data = json.load(f)
print("JSON LEIDO OK:", list(meta_data.keys()))

if cat_slug in meta_data:
    related_slugs = meta_data[cat_slug].get("relacionados", [])
    potential_products = []
    
    for cat in catalog:
        if cat.get("name") and slugify(cat["name"]) in related_slugs:
            for sub in cat.get("subcategories", []):
                potential_products.extend(sub.get("products", []))
                
    print("PRODUCTOS POTENCIALES:", len(potential_products))
else:
    print("EL SLUG NO ESTA EN EL JSON")
