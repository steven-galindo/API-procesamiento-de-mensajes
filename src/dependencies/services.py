from services.message_service import MessageProcessingService, MessageStorageService, MessageRetrievalService
from sqlalchemy.orm import Session
from fastapi import Depends
from core.database import get_db

def get_message_processing_service() -> MessageProcessingService:
    """Obtiene una instancia del servicio de procesamiento de mensajes."""
    return MessageProcessingService()

def get_storage_service(db: Session = Depends(get_db)) -> MessageStorageService:
    """Obtiene una instancia del servicio de almacenamiento de mensajes."""
    return MessageStorageService(db) 

def get_retrieval_service(db: Session = Depends(get_db)) -> MessageRetrievalService:
    """Obtiene una instancia del servicio de recuperación de mensajes."""
    return MessageRetrievalService(db)