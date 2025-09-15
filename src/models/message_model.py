from sqlalchemy import Column, String, Integer, DateTime
from core.database import Base

class MessageModel(Base):
    __tablename__ = "messages"
    
    message_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    content = Column(String)
    timestamp = Column(DateTime)
    sender = Column(String)
    word_count = Column(Integer, default=0, index=True)
    character_count = Column(Integer, default=0)
    processed_at = Column(DateTime)
