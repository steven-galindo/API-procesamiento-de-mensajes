from fastapi import Security
from core.auth import verify_api_key

def require_api_key(api_key=Security(verify_api_key)):
    """dependencia para requerir API Key en los endpoints"""
    return api_key
