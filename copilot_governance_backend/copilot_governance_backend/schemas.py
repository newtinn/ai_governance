from pydantic import BaseModel
from typing import Optional

# Schema for creating a KnowledgeSource
class KnowledgeSourceCreate(BaseModel):
    name: str

# Schema for associating a KnowledgeSource with an Agent
class AgentKnowledgeSourceCreate(BaseModel):
    agent_id: int
    knowledge_id: int