"""
VEA Connect - Aplicación Principal
Sistema de gestión de conocimiento para comunidad religiosa
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from api.search_routes import router as search_router
from api.chatbot_routes import router as chatbot_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="VEA Connect API",
    description="API para sistema de gestión de conocimiento de comunidad religiosa",
    version=Config.APP_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(search_router)
app.include_router(chatbot_router)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "VEA Connect API",
        "version": Config.APP_VERSION,
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Verificar estado del sistema"""
    return {
        "status": "healthy",
        "app_name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "debug": Config.DEBUG
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)
