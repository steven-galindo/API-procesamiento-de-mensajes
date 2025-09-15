from typing import Literal
from pydantic import BaseModel, validator, Field
from core.exceptions import SenderMissingException
from datetime import datetime

class MessageRequestSchema(BaseModel):
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: str 

    @validator('sender')
    def validate_sender(cls, v):
        if v not in ["user", "system"]:
            raise SenderMissingException()
        return v

class Metadata(BaseModel):
        word_count: int = 0
        character_count: int = 0
        processed_at: datetime = None

class DataResponseSchema(BaseModel):
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: str
    metadata: Metadata = Field(default_factory=Metadata)

class MessageResponseSchema(BaseModel):
    status: str
    data: DataResponseSchema = Field(default_factory=DataResponseSchema)

class MessagesListSchema(BaseModel):
    messages: list[MessageResponseSchema] = []
    total: int = 0 
    count: int = 0 