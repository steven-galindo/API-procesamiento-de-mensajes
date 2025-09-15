import pytest
from datetime import datetime
from services.message_service import MessageRetrievalService
from models.message_model import MessageModel
from schemas.message_schema import MessageResponseSchema
from core.exceptions import DatabaseException
from unittest.mock import Mock, patch

class TestMessageRetrievalService:
    
    @pytest.fixture
    def sample_messages(self, test_db):
        """Fixture que crea mensajes de prueba en la base de datos"""
        messages = [
            MessageModel(
                message_id="msg_001",
                session_id="session_001",
                content="Primer mensaje de la sesión 1",
                timestamp=datetime(2025, 9, 15, 10, 0, 0),
                sender="user",
                word_count=6,
                character_count=32,
                processed_at=datetime(2025, 9, 15, 10, 0, 5)
            ),
            MessageModel(
                message_id="msg_002",
                session_id="session_001",
                content="Segundo mensaje de la sesión 1",
                timestamp=datetime(2025, 9, 15, 10, 1, 0),
                sender="system",
                word_count=6,
                character_count=33,
                processed_at=datetime(2025, 9, 15, 10, 1, 5)
            ),
            MessageModel(
                message_id="msg_003",
                session_id="session_001",
                content="Tercer mensaje de user",
                timestamp=datetime(2025, 9, 15, 10, 2, 0),
                sender="user",
                word_count=4,
                character_count=25,
                processed_at=datetime(2025, 9, 15, 10, 2, 5)
            ),
            MessageModel(
                message_id="msg_004",
                session_id="session_002",
                content="Mensaje de otra sesión",
                timestamp=datetime(2025, 9, 15, 11, 0, 0),
                sender="user",
                word_count=4,
                character_count=24,
                processed_at=datetime(2025, 9, 15, 11, 0, 5)
            )
        ]
        
        # agregar a la base de datos
        for message in messages:
            test_db.add(message)
        test_db.commit()
        
        return messages
    
    def test_get_messages_by_session_basic(self, test_db, sample_messages):
        """Test básico de recuperación de mensajes por sesión"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # mensajes de session_001
        result = retrieval_service.get_messages_by_session("session_001")
        
        assert isinstance(result, list)
        assert len(result) == 3 
        
        # verificar que todos son MessageResponseSchema
        for message in result:
            assert isinstance(message, MessageResponseSchema)
            assert message.status == "success"
            assert message.data.session_id == "session_001"
        
        # verificar contenidos específicos
        contents = [msg.data.content for msg in result]
        assert "Primer mensaje de la sesión 1" in contents
        assert "Segundo mensaje de la sesión 1" in contents
        assert "Tercer mensaje de user" in contents
    
    def test_get_messages_by_session_with_sender_filter(self, test_db, sample_messages):
        """Test de recuperación con filtro por sender"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # Recuperar solo mensajes de user en session_001
        result = retrieval_service.get_messages_by_session(
            session_id="session_001",
            sender="user"
        )
        
        # verificaciones
        assert len(result) == 2  # solo 2 mensajes de user
        
        for message in result:
            assert message.data.sender == "user"
            assert message.data.session_id == "session_001"
        
        # verificar contenidos específicos
        contents = [msg.data.content for msg in result]
        assert "Primer mensaje de la sesión 1" in contents
        assert "Tercer mensaje de user" in contents
        assert "Segundo mensaje de la sesión 1" not in contents  # ✅ Este es de system
    
    def test_get_messages_by_session_with_pagination(self, test_db, sample_messages):
        """Test de paginación con limit y offset"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # recuperar primer página (limit=2, offset=0)
        page1 = retrieval_service.get_messages_by_session(
            session_id="session_001",
            limit=2,
            offset=0
        )
        
        assert len(page1) == 2
        
        # recuperar segunda página (limit=2, offset=2)
        page2 = retrieval_service.get_messages_by_session(
            session_id="session_001",
            limit=2,
            offset=2
        )
        
        assert len(page2) == 1  # solo queda 1 mensaje
        
        # verificar que no hay duplicados
        page1_ids = [msg.data.message_id for msg in page1]
        page2_ids = [msg.data.message_id for msg in page2]
        assert len(set(page1_ids + page2_ids)) == 3  # 3 IDs únicos
    
    def test_get_messages_by_session_empty_result(self, test_db, sample_messages):
        """Test cuando no hay mensajes para la sesión"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # buscar en una sesión que no existe
        result = retrieval_service.get_messages_by_session("session_999999")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_messages_by_session_empty_sender_filter(self, test_db, sample_messages):
        """Test cuando el filtro por sender no tiene resultados"""
        retrieval_service = MessageRetrievalService(test_db)
        
        result = retrieval_service.get_messages_by_session(
            session_id="session_002",
            sender="system"  # no hay mensajes de system en session_002
        )
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_convert_model_to_schema(self, test_db):
        """Test de conversión de modelo a schema"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # crear un modelo de prueba
        model = MessageModel(
            message_id="convert_test",
            session_id="session_convert",
            content="Mensaje para convertir",
            timestamp=datetime(2025, 9, 15, 12, 0, 0),
            sender="user",  # ✅ Solo user o system permitidos
            word_count=3,
            character_count=21,
            processed_at=datetime(2025, 9, 15, 12, 0, 5)
        )
        
        # convertir a schema
        result = retrieval_service._convert_model_to_schema(model)

        assert isinstance(result, MessageResponseSchema)
        assert result.status == "success"
        assert result.data.message_id == "convert_test"
        assert result.data.session_id == "session_convert"
        assert result.data.content == "Mensaje para convertir"
        assert result.data.sender == "user"
        assert result.data.metadata.word_count == 3
        assert result.data.metadata.character_count == 21
        assert result.data.metadata.processed_at == datetime(2025, 9, 15, 12, 0, 5)
    
    def test_get_messages_database_error(self, test_db):
        """Test de manejo de errores de base de datos"""
        retrieval_service = MessageRetrievalService(test_db)
        
        with patch.object(test_db, 'query', side_effect=Exception("DB Error simulado")):
            with pytest.raises(DatabaseException) as exc_info:
                retrieval_service.get_messages_by_session("session_001")
            
            assert "Error al recuperar mensajes de la sesión" in str(exc_info.value)
    
    def test_get_messages_complex_scenario(self, test_db, sample_messages):
        """Test de escenario complejo con múltiples filtros"""
        retrieval_service = MessageRetrievalService(test_db)
        
        # recuperar mensajes de session_001, sender=user, con paginación
        result = retrieval_service.get_messages_by_session(
            session_id="session_001",
            sender="user",
            limit=1,
            offset=0
        )
        
        assert len(result) == 1
        assert result[0].data.sender == "user"
        assert result[0].data.session_id == "session_001"
        
        # verificar que la estructura está completa
        message = result[0]
        assert message.status == "success"
        assert message.data.message_id is not None
        assert message.data.content is not None
        assert message.data.timestamp is not None
        assert message.data.metadata.word_count > 0
        assert message.data.metadata.character_count > 0
        assert message.data.metadata.processed_at is not None
    
