import json

with open("data/categorias_meta.json", "r") as f:
    meta_data = json.load(f)

# Corregimos la clave 
meta_data["vinilos-de-corte"] = meta_data.pop("vinilos-de-corte-oracal", {"relacionados": ["papel-posicionador"]})

with open("data/categorias_meta.json", "w") as f:
    json.dump(meta_data, f, indent=4)
