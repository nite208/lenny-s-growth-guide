from supabase import create_client
from config import settings
import structlog

log = structlog.get_logger()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

async def save_message(session_id: str, role: str, content: str):
    try:
        supabase.table("messages").insert({"session_id": session_id, "role": role, "content": content}).execute()
    except Exception as e:
        log.error("db_save_error", error=str(e))

async def get_session_history(session_id: str, limit: int = 10) -> list[dict]:
    try:
        result = supabase.table("messages").select("role,content").eq("session_id", session_id).order("created_at").limit(limit).execute()
        return [{"role": r["role"], "content": r["content"]} for r in result.data]
    except Exception as e:
        log.error("db_fetch_error", error=str(e))
        return []
