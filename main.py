import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import Routers
from routes import auth, ui, v2, cotizador_api, catalog_api, marketing_api, clientes_api, media_api, webhook

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(ui.router)
app.include_router(v2.router)
app.include_router(cotizador_api.router)
app.include_router(catalog_api.router)
app.include_router(marketing_api.router)
app.include_router(clientes_api.router)
app.include_router(media_api.router)
app.include_router(webhook.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
