from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
from core.exceptions import CustomValidationException, custom_rate_limit_exceeded_handler
from dotenv import load_dotenv
import os
from controllers import message_controller
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configuración de la app
limiter = Limiter(key_func=get_remote_address)
load_dotenv()
info_app = {"title": "API procesamiento de mensajes",
        "message": "API en funcionamiento",
        "version": f"{os.getenv('API_VERSION', '1.0.0')}"
    }

# Crear la app FastAPI
app = FastAPI(title=info_app["title"], version=info_app["version"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)


# CORS middleware para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear las tablas en la base de datos al iniciar la app
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Handler global de error en validación 422
app.add_exception_handler(RequestValidationError, CustomValidationException)

# Routers   
app.include_router(message_controller.router)

# Ruta raíz para health check
@app.get("/")
@limiter.limit("60/minute") 
def read_root(request: Request):
    return info_app

