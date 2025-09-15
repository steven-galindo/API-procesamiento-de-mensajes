import pytest
from core.auth import get_valid_api_key, verify_api_key
from core.exceptions import UnauthorizedException

def test_get_valid_api_key(test_api_key):
    """Test que la API key se obtiene correctamente"""
    api_key = get_valid_api_key()
    assert api_key == test_api_key
    assert api_key == "test-api-key-123"

def test_verify_api_key_valid(test_api_key):
    """Test con API key válida"""
    result = verify_api_key(test_api_key)
    assert result == test_api_key

def test_verify_api_key_invalid():
    """Test con API key inválida"""
    with pytest.raises(UnauthorizedException) as exc_info:
        verify_api_key("api-key-incorrecta")
    
    assert "API key inválida" in str(exc_info.value)

def test_verify_api_key_missing():
    """Test sin API key"""
    with pytest.raises(UnauthorizedException) as exc_info:
        verify_api_key(None)
    
    assert "Falta API Key" in str(exc_info.value)