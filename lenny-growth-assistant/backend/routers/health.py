from fastapi import APIRouter
from services.rag_service import rag_service
from services.llm_service import llm_service
from db.supabase_client import supabase

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
def health():
    try:
        count = rag_service.collection.count()
        try:
            supabase.table("sessions").select("id").limit(1).execute()
            db_ok = True
        except Exception:
            db_ok = False
        return {"status":"ok","provider":llm_service.get_provider_name(),"chroma_docs":count,"db_connected":db_ok}
    except Exception as e:
        return {"status":"degraded","error":str(e)}
