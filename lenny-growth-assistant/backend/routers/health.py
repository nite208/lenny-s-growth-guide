from fastapi import APIRouter
from services.rag_service import rag_service
from services.llm_service import llm_service
from db.supabase_client import is_db_connected

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def health():
    try:
        count = rag_service.collection.count()
        db_ok = is_db_connected()
        llm_connected = await llm_service.is_provider_connected()
        return {
            "status": "ok" if llm_connected and db_ok and count > 0 else "degraded",
            "provider": llm_service.get_provider_name(),
            "llm_connected": llm_connected,
            "chroma_docs": count,
            "chroma_ready": count > 0,
            "db_connected": db_ok
        }
    except Exception as e:
        return {"status":"degraded","error":str(e)}
