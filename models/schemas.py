from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric
from sqlalchemy.orm import declarative_base, relationship
import datetime
import uuid

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_email = Column(String(255), nullable=False)
    subject = Column(String(255))
    raw_body = Column(Text, nullable=False)
    assigned_category = Column(String(50), default="unassigned")
    current_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    logs = relationship("AgentExecutionLog", back_populates="ticket", cascade="all, delete-orphan")


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    model_used = Column(String(50), nullable=False)
    tool_invoked = Column(String(100))
    llm_reasoning = Column(Text)
    execution_status = Column(String(50), nullable=False)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="logs")
    rag_sources = relationship("RagReference", back_populates="execution_log", cascade="all, delete-orphan")


class RagReference(Base):
    __tablename__ = "rag_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(36), ForeignKey("agent_execution_logs.id", ondelete="CASCADE"), nullable=False)
    pinecone_vector_id = Column(String(100), nullable=False)
    retrieved_chunk_text = Column(Text, nullable=False)
    similarity_score = Column(Numeric(5, 4), nullable=False)

    execution_log = relationship("AgentExecutionLog", back_populates="rag_sources")