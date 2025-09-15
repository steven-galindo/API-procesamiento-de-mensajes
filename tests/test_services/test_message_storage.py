import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
from sqlalchemy.exc import SQLAlchemyError

from services.message_service import MessageStorageService
from models.message_model import MessageModel
from schemas.message_schema import MessageResponseSchema, DataResponseSchema, Metadata
from core.exceptions import DatabaseException

class TestMessageStorageService:
    
    def test_save_message_success(self, test_db):
        """Test de guardado exitoso de mensaje"""
        storage_service = MessageStorageService(test_db)

        metadata = Metadata(
            word_count=5,
            character_count=25,
            processed_at=datetime.now(timezone.utc)
        )
        
        data = DataResponseSchema(
            message_id="test_msg_001",
            session_id="session_001",
            content="Este es un mensaje de prueba",
            timestamp=datetime.now(timezone.utc),
            sender="user",
            metadata=metadata
        )
        
        message_response = MessageResponseSchema(
            status="success",
            data=data
        )
        
        # Ejecutar el método
        result = storage_service.save_message(message_response)
        
        # Verificaciones básicas
        assert isinstance(result, MessageModel)
        assert result.message_id == "test_msg_001"
        assert result.session_id == "session_001"
        assert result.content == "Este es un mensaje de prueba"
        assert result.sender == "user"
        assert result.word_count == 5
        assert result.character_count == 25
        assert result.processed_at is not None
        saved_message = test_db.query(MessageModel).filter(
            MessageModel.message_id == "test_msg_001"
        ).first()
        assert saved_message is not None
        assert saved_message.content == "Este es un mensaje de prueba"
    
    def test_save_message_integrity_error(self, test_db):
        """Test de error de integridad (mensaje duplicado)"""
        storage_service = MessageStorageService(test_db)
        
        # Crear mensaje con ID que ya existe
        metadata = Metadata(
            word_count=3,
            character_count=15,
            processed_at=datetime.now(timezone.utc)
        )
        
        data = DataResponseSchema(
            message_id="duplicate_msg",
            session_id="session_002",
            content="Mensaje original",
            timestamp=datetime.now(timezone.utc),
            sender="user",
            metadata=metadata
        )
        
        message_response = MessageResponseSchema(
            status="success",
            data=data
        )
        
        # guardar el primer mensaje 
        storage_service.save_message(message_response)
        
        # cambiar el contenido para simular duplicado
        data.content = "Mensaje duplicado"  
        
        # guardar el segundo mensaje 
        with pytest.raises(DatabaseException) as exc_info:
            storage_service.save_message(message_response)
        
        assert "Error de integridad" in str(exc_info.value)
        assert "duplicate_msg" in str(exc_info.value)
        assert "ya existe" in str(exc_info.value)
    
    def test_save_message_sqlalchemy_error(self, test_db):
        """Test de error de SQLAlchemy"""
        storage_service = MessageStorageService(test_db)

        # mock de la sesión para simular SQLAlchemyError
        mock_db = Mock()
        mock_db.add.side_effect = SQLAlchemyError("Error de conexión")
        mock_db.rollback = Mock()
        
        storage_service.db = mock_db
        
        metadata = Metadata(
            word_count=3,
            character_count=15,
            processed_at=datetime.now(timezone.utc)
        )
        
        data = DataResponseSchema(
            message_id="sql_error_msg",
            session_id="session_003",
            content="Mensaje con error SQL",
            timestamp=datetime.now(timezone.utc),
            sender="user",
            metadata=metadata
        )
        
        message_response = MessageResponseSchema(
            status="success",
            data=data
        )
        
        with pytest.raises(DatabaseException) as exc_info:
            storage_service.save_message(message_response)
        
        assert "Error de base de datos" in str(exc_info.value)
        mock_db.rollback.assert_called_once()
    
    def test_save_message_generic_exception(self, test_db):
        """Test de excepción genérica"""
        storage_service = MessageStorageService(test_db)
        
        # mock de la sesión para simular excepción genérica
        mock_db = Mock()
        mock_db.add.side_effect = Exception("Error inesperado")
        mock_db.rollback = Mock()
        
        storage_service.db = mock_db
        
        metadata = Metadata(
            word_count=4,
            character_count=20,
            processed_at=datetime.now(timezone.utc)
        )
        
        data = DataResponseSchema(
            message_id="generic_error_msg",
            session_id="session_004",
            content="Mensaje con error genérico",
            timestamp=datetime.now(timezone.utc),
            sender="user000",
            metadata=metadata
        )
        
        message_response = MessageResponseSchema(
            status="success",
            data=data
        )
        
        with pytest.raises(DatabaseException) as exc_info:
            storage_service.save_message(message_response)
        
        assert "Error inesperado al almacenar el mensaje" in str(exc_info.value)
        mock_db.rollback.assert_called_once()
    
    def test_save_message_rollback_called_on_error(self, test_db):
        """Test que verifica que rollback se llame en todos los errores"""
        storage_service = MessageStorageService(test_db)
        
        # Crear un mensaje válido
        metadata = Metadata(
            word_count=2,
            character_count=10,
            processed_at=datetime.now(timezone.utc)
        )
        
        data = DataResponseSchema(
            message_id="rollback_test",
            session_id="session_005",
            content="Test rollback",
            timestamp=datetime.now(timezone.utc),
            sender="user",
            metadata=metadata
        )
        
        message_response = MessageResponseSchema(
            status="success",
            data=data
        )
        
        # mock para interceptar llamadas
        original_rollback = test_db.rollback
        rollback_called = False
        
        def mock_rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()
        
        test_db.rollback = mock_rollback
        
        # simular error en commit
        original_commit = test_db.commit
        test_db.commit = Mock(side_effect=Exception("Error en commit"))
        
        with pytest.raises(DatabaseException):
            storage_service.save_message(message_response)
        
        assert rollback_called, "El rollback debería haberse llamado"
        
        # restaurar métodos originales
        test_db.commit = original_commit
        test_db.rollback = original_rollback