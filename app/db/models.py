from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    total_chunks = Column(Integer, nullable=False) 

    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    text = Column(Text)
    vector_id = Column(String)    # Qdrant id for chunk

    document = relationship("Document", back_populates="chunks")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('email', 'phone_number', 'date', 'time', name='unique_booking'),
    )