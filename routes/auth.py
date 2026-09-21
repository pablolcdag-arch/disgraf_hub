from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
import jwt
from datetime import datetime, timedelta, timezone
from dependencies import get_current_user, USERS, templates, JWT_SECRET_KEY, JWT_ALGORITHM

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        if user["role"] == "seller":
            return RedirectResponse(url="/cotizador", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = USERS.get(username)
    if not user or user["password"] != password:
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Credenciales inválidas"})
    
    # Create JWT session
    payload = {
        "username": username,
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    session_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    target_url = "/cotizador" if user["role"] == "seller" else "/dashboard"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response

