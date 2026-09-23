from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import FileResponse
from dependencies import get_current_user, DATA_DIR
import os
import shutil

router = APIRouter()
@router.post("/api/media/upload")
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

@router.get("/api/media/list")
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

@router.get("/media/file/{filename}")
async def media_serve_file(filename: str):
    media_dir = os.path.join(DATA_DIR, "media")
    file_path = os.path.join(media_dir, filename)
    
    # Try exact match first
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
        
    # If not found, try case-insensitive match
    if os.path.exists(media_dir):
        for f in os.listdir(media_dir):
            if f.lower() == filename.lower():
                from fastapi.responses import FileResponse
                return FileResponse(os.path.join(media_dir, f))
                
    return {"error": "File not found"}
