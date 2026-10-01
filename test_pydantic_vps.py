import json
import sys
from pydantic import BaseModel, ValidationError
from typing import List, Optional

class ComprobanteItem(BaseModel):
    producto_id: str
    descripcion: str
    cantidad: float
    precio_unitario: float
    alicuota_iva: float
    subtotal: float

class ComprobanteCreate(BaseModel):
    cliente_id: str
    tipo_comprobante: str
    numero_comprobante: Optional[str] = None
    fecha_emision: Optional[str] = None
    subtotal: float
    total_iva: float
    total: float
    items: List[ComprobanteItem]
    iva_reducido: bool = False
    comprobante_asociado_id: Optional[int] = None
    facturar_afip: Optional[bool] = False
    forma_pago: Optional[str] = None

payload = {
    "cliente_id": "1748",
    "tipo_comprobante": "Nota de Crédito A",
    "subtotal": 103332.14,
    "total_iva": 21699.75,
    "total": 125031.89,
    "items": [
        {
            "producto_id": "1",
            "descripcion": "Posicionador",
            "cantidad": 1,
            "precio_unitario": 93817.60,
            "alicuota_iva": 21.0,
            "subtotal": 93817.60
        }
    ],
    "facturar_afip": True,
    "comprobante_asociado_id": "82"
}

try:
    c = ComprobanteCreate(**payload)
    print("SUCCESS")
except ValidationError as e:
    print("FAILED")
    print(e.json())
