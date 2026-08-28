from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: Literal["chat","essay","artifact"] = "chat"

class ArtifactData(BaseModel):
    type: Literal["markdown","html"]
    content: str

class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: list[str] = []
    artifact: Optional[ArtifactData] = None
    provider: str
    timestamp: datetime = datetime.utcnow()

class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
