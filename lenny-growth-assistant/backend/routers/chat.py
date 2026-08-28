from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.llm_service import llm_service
from services.rag_service import rag_service
from services.essay_service import generate_essay
from db.supabase_client import save_message, get_session_history
import uuid, structlog

router = APIRouter(prefix="/api/chat", tags=["chat"])
log = structlog.get_logger()

RAG_SYSTEM = """You are The Lenny Growth Assistant — expert on product management and growth.
RULES:
1. Answer ONLY from the provided transcript context. Do not hallucinate.
2. If context is insufficient say: "I don't have enough information in Lenny's transcripts to answer this confidently."
3. Always cite sources as (Source: Episode Title).
4. Be concise, specific, and actionable."""

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        chunks = rag_service.retrieve(req.message)
        context = rag_service.format_context(chunks)
        history = await get_session_history(session_id)
        if req.mode == "essay":
            response_text = await generate_essay(req.message, context, history)
            artifact = {"type": "markdown", "content": response_text}
        elif req.mode == "artifact":
            system = "Generate a complete self-contained HTML/CSS page with inline styles. No JavaScript. Return only HTML."
            response_text = await llm_service.chat(messages=[{"role":"user","content":f"Context:\n{context}\n\nRequest: {req.message}"}], system=system)
            artifact = {"type": "html", "content": response_text}
        else:
            messages = history + [{"role":"user","content":f"Context:\n{context}\n\nQuestion: {req.message}"}]
            response_text = await llm_service.chat(messages=messages, system=RAG_SYSTEM)
            artifact = None
        await save_message(session_id, "user", req.message)
        await save_message(session_id, "assistant", response_text)
        return ChatResponse(session_id=session_id, message=response_text, sources=[c["source"] for c in chunks], artifact=artifact, provider=llm_service.get_provider_name())
    except Exception as e:
        log.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
