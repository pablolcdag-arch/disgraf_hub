from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from dependencies import get_current_user, templates

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    if user["role"] == "seller":
        return RedirectResponse(url="/cotizador", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user})

@router.get("/precios", response_class=HTMLResponse)
async def precios_page(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="precios.html", context={"user": user})

@router.get("/cotizador", response_class=HTMLResponse)
async def cotizador_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(request=request, name="cotizador.html", context={"user": user})

@router.get("/clientes", response_class=HTMLResponse)
async def clientes_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="clientes.html", context={"user": user})

@router.get("/media", response_class=HTMLResponse)
async def media_page(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="media.html", context={"user": user})

@router.get("/marketing", response_class=HTMLResponse)
async def marketing_page(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="marketing.html", context={"user": user})

@router.get("/satellite-demo", response_class=HTMLResponse)
async def satellite_demo_page(request: Request):
    return templates.TemplateResponse(request=request, name="satellite_demo.html")

