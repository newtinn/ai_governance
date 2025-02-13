from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    display_name = Column(String)
    description = Column(String)
    owner = Column(String)
    owner_email = Column(String)
    model_base = Column(String)
    location = Column(String)
    active = Column(Boolean)
    status = Column(String)
    budget = Column(Float)
    workspace = Column(String)
    openai_endpoint = Column(String, nullable=True)
    openai_api_key = Column(String, nullable=True)

    # Establish relationship to AgentKnowledgeSource
    knowledge_sources = relationship("AgentKnowledgeSource", back_populates="agent")

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    source = Column(String)
    approved = Column(Boolean)

    # Establish relationship to AgentKnowledgeSource
    agent_associations = relationship("AgentKnowledgeSource", back_populates="knowledge_source")

class AgentKnowledgeSource(Base):
    __tablename__ = "agent_knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge_sources.id"), index=True)

    # Define relationships to Agent and KnowledgeSource
    agent = relationship("Agent", back_populates="knowledge_sources")
    knowledge_source = relationship("KnowledgeSource", back_populates="agent_associations")