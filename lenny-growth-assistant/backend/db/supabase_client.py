from supabase import create_client
from config import settings
import structlog
from datetime import datetime

log = structlog.get_logger()
supabase = None
_memory_sessions: dict[str, dict] = {}
_memory_messages: list[dict] = []

if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as e:
        log.error("db_client_init_error", error=str(e))
else:
    log.warning("db_client_not_configured", reason="missing_supabase_credentials")


def _now():
    return datetime.utcnow().isoformat()


def is_db_connected() -> bool:
    if supabase is None:
        return False
    try:
        supabase.table("sessions").select("id").limit(1).execute()
        return True
    except Exception:
        return False

async def save_message(session_id: str, role: str, content: str):
    payload = {"session_id": session_id, "role": role, "content": content, "created_at": _now()}
    try:
        if supabase is None:
            raise RuntimeError("supabase_unavailable")
        supabase.table("messages").insert(payload).execute()
    except Exception as e:
        log.error("db_save_error", error=str(e))
        _memory_messages.append(payload)

async def get_session_history(session_id: str, limit: int = 10) -> list[dict]:
    try:
        if supabase is None:
            raise RuntimeError("supabase_unavailable")
        result = supabase.table("messages").select("role,content").eq("session_id", session_id).order("created_at").limit(limit).execute()
        return [{"role": r["role"], "content": r["content"]} for r in result.data]
    except Exception as e:
        log.error("db_fetch_error", error=str(e))
        local = [m for m in _memory_messages if m["session_id"] == session_id]
        return [{"role": m["role"], "content": m["content"]} for m in local[-limit:]]


def create_session_record(session_id: str, title: str):
    payload = {"id": session_id, "title": title, "created_at": _now()}
    try:
        if supabase is None:
            raise RuntimeError("supabase_unavailable")
        supabase.table("sessions").insert({"id": session_id, "title": title}).execute()
        return {"session_id": session_id, "title": title}
    except Exception as e:
        log.error("db_create_session_error", error=str(e))
        _memory_sessions[session_id] = payload
        return {"session_id": session_id, "title": title}


def list_session_records(limit: int = 20):
    try:
        if supabase is None:
            raise RuntimeError("supabase_unavailable")
        return supabase.table("sessions").select("*").order("created_at", desc=True).limit(limit).execute().data
    except Exception as e:
        log.error("db_list_sessions_error", error=str(e))
        items = sorted(_memory_sessions.values(), key=lambda s: s.get("created_at", ""), reverse=True)
        return items[:limit]


def list_session_messages(session_id: str):
    try:
        if supabase is None:
            raise RuntimeError("supabase_unavailable")
        return supabase.table("messages").select("*").eq("session_id", session_id).order("created_at").execute().data
    except Exception as e:
        log.error("db_list_messages_error", error=str(e))
        return [m for m in _memory_messages if m["session_id"] == session_id]
