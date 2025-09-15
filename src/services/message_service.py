import json
import os
import string
from datetime import datetime, timezone
import pytz
from typing import List, Optional

from fuzzywuzzy import fuzz
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from core.exceptions import BannedWordException, DatabaseException
from models.message_model import MessageModel
from schemas.message_schema import MessageRequestSchema, MessageResponseSchema, Metadata, DataResponseSchema

class MessageProcessingService:
    """
    Servicio para procesar mensajes, esta clase se encarga de:
    - Validar y filtrar palabras prohibidas usando un corpus con similitud.
    - Añadir metadatos: conteo de palabras, caracteres y timestamp de procesamiento.
    """
    def __init__(self):
        """
        Inicializa el servicio cargando el corpus de palabras prohibidas y configurando parámetros.
        """
        self.corpus_filter_path =  os.getenv('CORPUS_FILE_PATH', os.path.join('data', 'corpus_filter.json'))
        self.similarity_threshold = 80
        self._punctuation_table = str.maketrans('', '', string.punctuation)
        self.tz = self._get_timezone()

    def _load_corpus(self) -> dict:
        """ Carga el corpus de palabras prohibidas desde un archivo JSON en la carpeta data/ """
        with open(self.corpus_filter_path, 'r') as f:
            return json.load(f)
    
    def _contains_banned_words(self, message: str) -> bool:
        """ Verifica si el mensaje contiene palabras prohibidas con similitud usando fuzzy matching """
        corpus = self._load_corpus()
        banned_words = [w.lower() for w in corpus.get("banned_words", [])]
        message = message.translate(self._punctuation_table)
        tokens = message.lower().split()
        for token in tokens:
            for banned in banned_words:
                if fuzz.ratio(token, banned) >= self.similarity_threshold:
                    return banned
        return None
    
    def _get_timezone(self) -> timezone:
        """ Obtiene la zona horaria configurada en las variables de entorno """
        tz = os.getenv('API_TIMEZONE', 'UTC')
        if tz == 'UTC':
            return timezone.utc
        else:
            return pytz.timezone(tz)
    
    def _count_words(self, message: str) -> int:
        """ Cuenta el número de palabras en un mensaje """
        return len(message.split())

    def _count_characters(self, message: str) -> int:
        """ Cuenta el número de caracteres en un mensaje """
        return len(message)

    def process_message(self, message_data: MessageRequestSchema) -> MessageResponseSchema:
        """ Procesa el mensaje, valida y añade metadatos 
            - Lanza BannedWordException si se detecta una palabra prohibida
            Entrada:
            - MessageRequestSchema
            Salida:
            - MessageResponseSchema
        """
        banned_word = self._contains_banned_words(message_data.content)
        if banned_word:
            raise BannedWordException(word=banned_word)

        data = DataResponseSchema(
            message_id=message_data.message_id,
            session_id=message_data.session_id,
            content=message_data.content,
            timestamp=message_data.timestamp,
            sender=message_data.sender,
            metadata=Metadata(
                word_count=self._count_words(message_data.content),
                character_count=self._count_characters(message_data.content),
                processed_at=datetime.now(tz=self.tz)
            )
        )

        response = MessageResponseSchema(
            status="success",
            data=data
        )

        return response

class MessageStorageService:
    """
    Servicio para almacenar mensajes procesados en la base de datos.
    """
    def __init__(self, db: Session):
        self.db = db

    def save_message(self, message: MessageResponseSchema) -> MessageModel: 
        """ Almacena el mensaje procesado en la base de datos.
            Lanza DatabaseException en caso de errores.
            Entrada:
            - MessageResponseSchema
            Salida:
            - MessageModel (objeto ORM)
        """
        try:
            db_message = MessageModel(
                message_id=message.data.message_id,
                session_id=message.data.session_id,
                content=message.data.content,
                timestamp=message.data.timestamp,
                sender=message.data.sender,
                word_count=message.data.metadata.word_count,
                character_count=message.data.metadata.character_count,
                processed_at=message.data.metadata.processed_at
            )
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            return db_message
            
        except IntegrityError as e:
            self.db.rollback()  
            raise DatabaseException(f"Error de integridad: mensaje con ID '{message.data.message_id}' ya existe")
            
        except SQLAlchemyError as e:
            self.db.rollback() 
            raise DatabaseException(f"Error de base de datos: {str(e)}")
            
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Error inesperado al almacenar el mensaje: {str(e)}")

class MessageRetrievalService:
    """Servicio para recuperar mensajes de la base de datos según filtros"""
    def __init__(self, db: Session):
        self.db = db

    def _convert_model_to_schema(self, model: MessageModel) -> MessageResponseSchema:
        """ Convierte un objeto ORM MessageModel a MessageResponseSchema """
        metadata = Metadata(
            word_count=model.word_count,
            character_count=model.character_count,
            processed_at=model.processed_at
        )
        data = DataResponseSchema(
            message_id=model.message_id,
            session_id=model.session_id,
            content=model.content,
            timestamp=model.timestamp,
            sender=model.sender,
            metadata=metadata
        )
        return MessageResponseSchema(
            status="success",
            data=data
        )

    def get_messages_by_session(
        self, 
        session_id: str, 
        limit: int = 100, 
        offset: int = 0, 
        sender: Optional[str] = None
    ) -> List[MessageResponseSchema]:
        """ Recupera mensajes de la base de datos filtrando por session_id, opcionalmente por sender.
            Lanza DatabaseException en caso de errores."""
        try:
            query = self.db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            )
            
            if sender:
                query = query.filter(MessageModel.sender == sender)
            
            db_messages = query.offset(offset).limit(limit).all()

            return [self._convert_model_to_schema(msg) for msg in db_messages]
            
        except Exception as e:
            raise DatabaseException(f"Error al recuperar mensajes de la sesión: {str(e)}")

