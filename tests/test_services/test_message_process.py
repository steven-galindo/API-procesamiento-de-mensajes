import pytest
import os
import tempfile
import json
import pytz
from unittest.mock import patch
from services.message_service import MessageProcessingService
from core.exceptions import BannedWordException

class TestMessageProcessingService:
    # tests para conteo de palabras y caracteres
    def test_count_words_simple(self):
        """Test básico de conteo de palabras"""
        service = MessageProcessingService()
        
        # Casos simples
        assert service._count_words("mensaje prueba") == 2
        assert service._count_words("una sola palabra") == 3
        assert service._count_words("") == 0
        assert service._count_words("   espacios   extra   ") == 2
    
    def test_count_characters_simple(self):
        """Test básico de conteo de caracteres"""
        service = MessageProcessingService()
        
        # Casos simples
        assert service._count_characters("test") == 4
        assert service._count_characters("hola mundo") == 10
        assert service._count_characters("") == 0
        assert service._count_characters("   ") == 3  
    # tests para configurar la zona horaria
    def test_get_timezone_default(self):
        """Test de timezone por defecto"""
        service = MessageProcessingService()
        
        # Sin variable de entorno
        with patch.dict(os.environ, {}, clear=True):
            timezone = service._get_timezone()
            assert timezone == timezone.utc
    
    def test_get_timezone_custom(self):
        """Test de timezone personalizado"""
        service = MessageProcessingService()
        # Con variable de entorno
        with patch.dict(os.environ, {"TIMEZONE": "America/Mexico_City"}):
            timezone = service._get_timezone()
            expected_tz = pytz.timezone("America/Mexico_City")
            assert str(timezone) == str(expected_tz)

    # tests para carga de corpus
    def test_load_corpus_success(self, mock_corpus_file):
        """Test de carga exitosa del corpus"""
        service = MessageProcessingService()

        corpus = service._load_corpus()
        # Verifica la estructura del corpus cargado
        assert "banned_words" in corpus
        assert isinstance(corpus["banned_words"], list)
        assert "scam" in corpus["banned_words"]
        assert "fraude" in corpus["banned_words"]
        assert len(corpus["banned_words"]) == 4  # scam, fraude, estafa, robo
    
    def test_load_corpus_file_not_found(self):
        """Test cuando el archivo de corpus no existe"""
        service = MessageProcessingService()
        
        # Configurar una ruta que no existe
        with patch.dict(os.environ, {"CORPUS_FILE_PATH": "/ruta/que/no/existe.json"}):
            with pytest.raises(FileNotFoundError):
                service._load_corpus()
    
    def test_load_corpus_invalid_json(self):
        """Test con archivo JSON inválido"""
        # Crear archivo temporal con JSON inválido
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content ")
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {"CORPUS_FILE_PATH": temp_path}):
                service = MessageProcessingService()  # ← Crear DENTRO del patch
                with pytest.raises(json.JSONDecodeError):
                    service._load_corpus()
        finally:
            os.unlink(temp_path)
            
    # tests para detección de palabras prohibidas
    def test_contains_banned_words_exact_match(self, mock_corpus_file):
        """Test de palabra prohibida con match exacto"""
        service = MessageProcessingService()
        assert service._contains_banned_words("Este mensaje tiene scam") == "scam"
        assert service._contains_banned_words("Cuidado con el fraude") == "fraude"
        assert service._contains_banned_words("Es una estafa") == "estafa"
        assert service._contains_banned_words("Intento de robo") == "robo"
        assert service._contains_banned_words("Mensaje normal sin problemas") is None
    
    def test_contains_banned_words_case_insensitive(self, mock_corpus_file):
        """Test que la detección ignore mayúsculas/minúsculas"""
        service = MessageProcessingService()
        assert service._contains_banned_words("SCAM en mayúsculas") == "scam"
        assert service._contains_banned_words("Fraude con mayúscula inicial") == "fraude"
        assert service._contains_banned_words("ESTAFA completa") == "estafa"
        assert service._contains_banned_words("robo en minúsculas") == "robo"
    
    def test_contains_banned_words_with_punctuation(self, mock_corpus_file):
        """Test que ignore puntuación"""
        service = MessageProcessingService()
        assert service._contains_banned_words("¡Es un scam!") == "scam"
        assert service._contains_banned_words("Fraude, cuidado.") == "fraude"
        assert service._contains_banned_words("¿Estafa?") == "estafa"
        assert service._contains_banned_words("Robo: evítalo") == "robo"
    
    def test_contains_banned_words_fuzzy_match(self, mock_corpus_file):
        """Test de fuzzy matching (palabras similares)"""
        service = MessageProcessingService()
        
        # Variaciones con typos que deberían detectarse (similarity >= 90%)
        assert service._contains_banned_words("Esto es un scaam") == "scam"  
        assert service._contains_banned_words("fraued bancario") == "fraude" 
        # Palabras muy diferentes que NO deberían detectarse
        assert service._contains_banned_words("palabra muy diferente") is None
        assert service._contains_banned_words("hola mundo") is None
    
    def test_process_message_success(self, mock_corpus_file):
        """Test de procesamiento exitoso de mensaje"""
        service = MessageProcessingService()
        
        # Crear un mensaje de prueba válido
        from schemas.message_schema import MessageRequestSchema
        from datetime import datetime
        
        message_data = MessageRequestSchema(
            message_id="test_123",
            session_id="session_001",
            content="Hola, este es un mensaje normal",
            timestamp=datetime.now(),
            sender="user" 
        )
        
        result = service.process_message(message_data)
        
        # Verificar la respuesta
        assert result.status == "success"
        assert result.data.content == "Hola, este es un mensaje normal"
        assert result.data.message_id == "test_123"
        assert result.data.session_id == "session_001"
        assert result.data.sender == "user"
        assert result.data.metadata.word_count == 6 
        assert result.data.metadata.character_count == 31
    
    def test_process_message_with_banned_word(self, mock_corpus_file):
        """Test que lance excepción con palabra prohibida"""
        service = MessageProcessingService()
        
        from schemas.message_schema import MessageRequestSchema
        from datetime import datetime
        
        message_data = MessageRequestSchema(
            message_id="test_456",
            session_id="session_002", 
            content="Este mensaje contiene scam",
            timestamp=datetime.now(),
            sender="user"
        )
        
        # BannedWordException
        with pytest.raises(BannedWordException) as exc_info:
            service.process_message(message_data)
        
        # Verificar que la excepción contiene la palabra prohibida
        assert "scam" in str(exc_info.value)
    
    

