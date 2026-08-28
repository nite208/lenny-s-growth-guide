from fastapi import APIRouter
from models.schemas import SessionCreate
from db.supabase_client import create_session_record, list_session_records, list_session_messages
import uuid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("/")
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    return create_session_record(sid, body.title)

@router.get("/")
def list_sessions():
    return list_session_records(limit=20)

@router.get("/{session_id}/messages")
def get_messages(session_id: str):
    return list_session_messages(session_id)
