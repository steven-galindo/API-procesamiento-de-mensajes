from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from fastapi import HTTPException
from typing import Optional
# Excepción para campo 'sender' inválido
class SenderMissingException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "error": {
                    "code": "SENDER_MISSING",
                    "message": "Error en el campo 'sender'",
                    "details": "El campo 'sender' debe ser 'user' o 'system'.",
                }
            }
        )

# Excepción personalizada para palabras prohibidas
class BannedWordException(HTTPException):
    def __init__(self, word: str):
        super().__init__(
            status_code=HTTP_400_BAD_REQUEST,
            detail={ 
                "status": "error",
                "error": {
                    "code": "BANNED_WORD_DETECTED",
                    "message": f"El mensaje contiene una palabra prohibida: '{word}'",
                    "details": []
                }
            }
        )

# función handler excepción personalizada para errores de validación 422
async def CustomValidationException(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Error de validación en los datos enviados",
                "details": "Los datos proporcionados no cumplen con el esquema esperado.",
            }
        }
    )

# Excepción por error en base de datos
class DatabaseException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Error al interactuar con la base de datos.",
                    "details": detail
                }
            }
        )

class MessagesNotFoundException(HTTPException):
    def __init__(self, session_id: str, sender: Optional[str] = None):
        message = f"No se encontraron mensajes para la sesión '{session_id}'"
        if sender:
            message += f" y el remitente '{sender}'"
        
        super().__init__(
            status_code=404,
            detail={
                "status": "error",
                "error": {
                    "code": "MESSAGES_NOT_FOUND",
                    "message": message,
                    "details": []
                }
            }
        )

# Excepción para API Key inválida
class UnauthorizedException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "error": {
                    "code": "INVALID_API_KEY",
                    "message": message,
                    "details": []
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

# Handler personalizado para Rate Limiting de slowapi
async def custom_rate_limit_exceeded_handler(request: Request, exc):
    # Extraer información del error de slowapi
    limit_info = str(exc.detail) if hasattr(exc, 'detail') else "límite excedido"
    retry_after = getattr(exc, 'retry_after', None)
    
    response_content = {
        "status": "error",
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"Límite de tasa excedido: {limit_info}",
            "details": "Has excedido el número máximo de solicitudes permitidas. Intenta de nuevo más tarde."
        }
    }
    
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)
    
    return JSONResponse(
        status_code=429,
        content=response_content,
        headers=headers
    )