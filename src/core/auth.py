from fastapi.security.api_key import APIKeyHeader
from fastapi import Security
from core.exceptions import UnauthorizedException
import os

# Configuración de API Keys
def get_valid_api_key():
    """Obtiene la API Key válida desde las variables de entorno."""
    return os.getenv("API_KEY", "api-key-default-123")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """Verifica que la API Key proporcionada sea válida."""
    if not api_key:
        raise UnauthorizedException(message="Falta API Key en el header 'X-API-Key'")

    valid_api_key = get_valid_api_key()
    if api_key != valid_api_key:
        raise UnauthorizedException(message="API key inválida o no autorizada")
    return api_key
