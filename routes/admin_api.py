from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from dependencies import get_current_user
from backup_service import generate_backup_zip
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Error eliminando archivo temporal {path}: {e}")

@router.get("/backup")
async def get_backup(request: Request, background_tasks: BackgroundTasks):
    """Genera un archivo ZIP del directorio de datos y lo devuelve para descargar."""
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol de admin.")
        
    try:
        zip_filepath = generate_backup_zip()
        if not os.path.exists(zip_filepath):
            raise HTTPException(status_code=500, detail="Error generando el archivo de backup.")
            
        background_tasks.add_task(remove_file, zip_filepath)
        return FileResponse(
            path=zip_filepath, 
            filename=os.path.basename(zip_filepath),
            media_type='application/zip'
        )


    except Exception as e:
        logger.error(f"Error en endpoint de backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
