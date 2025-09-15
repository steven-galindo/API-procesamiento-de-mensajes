import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from models.message_model import MessageModel
from main import app
from core.database import Base, get_db

# bd de pruebas
@pytest.fixture(scope="function")
def test_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Crea una sesión de base de datos limpia para cada test"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    # limpiar todas las tablas antes de cada test
    session.query(MessageModel).delete()
    session.commit()
    
    try:
        yield session
    finally:
        session.rollback()  # ← Agregar rollback
        session.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Cliente de prueba de FastAPI que usa la BD de test"""
    def override_get_db():
        yield test_db 

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

# test de api key
@pytest.fixture(scope="session")
def test_api_key():
    """API Key válida para tests"""
    return "test-api-key-123"

@pytest.fixture(scope="function")
def auth_headers(test_api_key):
    """Headers con API Key para requests autenticados"""
    return {"X-API-Key": test_api_key}

# mock corpus de palabras baneadas
@pytest.fixture(scope="session")
def mock_corpus_data():
    """Datos de corpus para tests"""
    return {
        "banned_words": [
            "scam",
            "fraude",
            "estafa",
            "robo"
        ]
    }

@pytest.fixture(scope="function")
def mock_corpus_file(mock_corpus_data):
    """Crea un archivo temporal con datos de corpus"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        import json
        json.dump(mock_corpus_data, f)
        temp_path = f.name
    
    with patch.dict(os.environ, {'CORPUS_FILE_PATH': temp_path}):
        yield temp_path
    
    # Limpia el archivo temporal
    os.unlink(temp_path)

# mensajes de prueba
@pytest.fixture
def sample_message_data():
    """Datos de mensaje válido para tests"""
    return {
        "content": "Hola, este es un mensaje de prueba",
        "sender": "user",
        "session_id": "session_test_001"
    }

@pytest.fixture
def sample_banned_message_data():
    """Datos de mensaje con palabra prohibida"""
    return {
        "content": "Este mensaje contiene es de un scam",
        "sender": "user", 
        "session_id": "session_test_002"
    }

# variables de entorno para tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_api_key):
    """Configura variables de entorno para tests"""
    test_env = {
        "API_KEY": test_api_key,
        "DATABASE_URL": "sqlite:///:memory:",
        "TIMEZONE": "America/Mexico_City"
    }
    
    with patch.dict(os.environ, test_env):
        yield