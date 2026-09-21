import os
from fastapi import Request
from fastapi.templating import Jinja2Templates
from google import genai

# Configurar directorio de datos
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

# Templates
templates = Jinja2Templates(directory="templates")

# Globals API y config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# In-memory mock DB for sessions (cookie based for UI simplicity)
sessions = {}

# Users Mock DB
USERS = {
    os.getenv("ADMIN_USERNAME", "pablo"): {"password": os.getenv("ADMIN_PASSWORD", "admin"), "role": "admin"},
    os.getenv("SELLER_USERNAME", "ventas"): {"password": os.getenv("SELLER_PASSWORD", "ventas"), "role": "seller"},
}

def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        return None
    return sessions[session_token]

