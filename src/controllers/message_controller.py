from fastapi import APIRouter, Depends, Query, Security, Request
from dependencies.services import get_message_processing_service, get_storage_service, get_retrieval_service
from dependencies.auth import require_api_key
from services.message_service import MessageProcessingService, MessageStorageService, MessageRetrievalService
from schemas.message_schema import MessageRequestSchema, MessageResponseSchema, MessagesListSchema
from core.exceptions import SenderMissingException, MessagesNotFoundException
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# limiter para configurar un máximo de requests por IP
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Messages router"], prefix="/api/messages")

@router.post("/")
@limiter.limit("100/hour") 
def receive_message(
    request: Request,
    message: MessageRequestSchema,
    api_key: str = Security(require_api_key),
    service: MessageProcessingService = Depends(get_message_processing_service),
    storage_service: MessageStorageService = Depends(get_storage_service),
) -> MessageResponseSchema:
    """Recibe y procesa un mensaje, luego lo almacena en la base de datos."""
    processed_message = service.process_message(message)
    storage_service.save_message(processed_message)
    return processed_message

@router.get("/{session_id}")
@limiter.limit("500/hour") 
def get_messages_by_session(
    request: Request,
    session_id: str,
    api_key: str = Security(require_api_key),
    limit: int = Query(default=100, ge=1, le=1000, description="Número máximo de mensajes a devolver"),
    offset: int = Query(default=0, ge=0, description="Número de mensajes a omitir"),
    sender: Optional[str] = Query(default=None, description="Filtrar por remitente (user/system)"),
    retrieval_service: MessageRetrievalService = Depends(get_retrieval_service)
) -> MessagesListSchema:
    """Recupera mensajes por session_id, con paginación y filtro opcional por remitente."""
    if sender and sender not in ["user", "system"]:
        raise SenderMissingException()
    
    messages = retrieval_service.get_messages_by_session(
        session_id=session_id,
        limit=limit,
        offset=offset,
        sender=sender
    )
    
    if not messages:
        raise MessagesNotFoundException(session_id, sender)
    
    return MessagesListSchema(
        messages=messages,
        total=len(messages),
        count=len(messages)
    )
