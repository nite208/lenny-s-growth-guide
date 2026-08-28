from fastapi import APIRouter
from models.schemas import SessionCreate
from db.supabase_client import supabase
import uuid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("/")
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    supabase.table("sessions").insert({"id": sid, "title": body.title}).execute()
    return {"session_id": sid, "title": body.title}

@router.get("/")
def list_sessions():
    return supabase.table("sessions").select("*").order("created_at", desc=True).limit(20).execute().data

@router.get("/{session_id}/messages")
def get_messages(session_id: str):
    return supabase.table("messages").select("*").eq("session_id", session_id).order("created_at").execute().data
