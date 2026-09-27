from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from dependencies import get_current_user
from backup_service import generate_backup_zip
import os
import logging
import tempfile
import zipfile
import shutil

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

@router.post("/restore")
async def restore_backup(request: Request, file: UploadFile = File(...)):
    """Restaura un archivo ZIP de backup al directorio de datos."""
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol de admin.")
        
    try:
        # Asume que el directorio data está en el nivel superior al router
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip_path = os.path.join(temp_dir, "uploaded_backup.zip")
            
            # Guardar el archivo subido
            with open(temp_zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extraer contenido
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Verificar base de datos
            db_path = os.path.join(extract_dir, "disgraf_hub.db")
            if not os.path.exists(db_path):
                raise HTTPException(status_code=400, detail="El archivo ZIP es inválido: falta disgraf_hub.db")
                
            # Sobreescribir data/ (Python 3.8+ permite dirs_exist_ok en copytree)
            shutil.copytree(extract_dir, data_dir, dirs_exist_ok=True)
            
        return {"status": "ok", "message": "Backup restaurado con éxito"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restaurando backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
