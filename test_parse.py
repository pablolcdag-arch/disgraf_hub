from pydantic import BaseModel
from typing import Optional

class C(BaseModel):
    comprobante_asociado_id: Optional[int] = None

print(C(**{"comprobante_asociado_id": "81"}).comprobante_asociado_id)
