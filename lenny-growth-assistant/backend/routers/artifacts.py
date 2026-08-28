from fastapi import APIRouter
from pydantic import BaseModel
from services.llm_service import llm_service
from services.rag_service import rag_service

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

class ArtifactRequest(BaseModel):
    prompt: str
    artifact_type: str = "markdown"

@router.post("/")
async def generate_artifact(req: ArtifactRequest):
    chunks = rag_service.retrieve(req.prompt)
    if len(chunks) == 0:
        return {
            "type": req.artifact_type,
            "content": "I don't have enough information in Lenny's transcripts to answer this",
            "sources": [],
        }
    context = rag_service.format_context(chunks)
    system = "Generate complete self-contained HTML/CSS. No JS. Return only HTML." if req.artifact_type == "html" else "Generate well-structured Markdown. Return only Markdown."
    content = await llm_service.chat(messages=[{"role":"user","content":f"Context:\n{context}\n\nRequest: {req.prompt}"}], system=system)
    return {"type": req.artifact_type, "content": content, "sources": [c["source"] for c in chunks]}
