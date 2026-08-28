# Lenny's Growth Guide

Build a full-stack app called "The Lenny Growth Assistant". Create ALL files — React frontend AND FastAPI backend — exactly as follows.

PROJECT STRUCTURE:
lenny-growth-assistant/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routers/chat.py
│   ├── routers/sessions.py
│   ├── routers/artifacts.py
│   ├── routers/health.py
│   ├── services/llm_service.py
│   ├── services/rag_service.py
│   ├── services/ingest_service.py
│   ├── services/essay_service.py
│   ├── models/schemas.py
│   ├── db/supabase_client.py
│   ├── ingest/run_ingest.py
│   └── tests/test_chat.py
├── frontend/
│   ├── src/App.jsx
│   ├── src/components/ChatPane.jsx
│   ├── src/components/MessageBubble.jsx
│   ├── src/components/ArtifactViewer.jsx
│   ├── src/components/ModelBadge.jsx
│   ├── src/components/SessionSidebar.jsx
│   ├── src/api/client.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md

=== backend/config.py ===
from pydantic_settings import BaseSettings
from enum import Enum

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class Settings(BaseSettings):
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    CHROMA_PERSIST_PATH: str = "./chroma_db"
    MAX_CHUNKS_PER_QUERY: int = 5
    MAX_SESSION_HISTORY: int = 10
    class Config:
        env_file = ".env"

settings = Settings()

=== backend/services/llm_service.py ===
import anthropic
import httpx
from config import settings, LLMProvider

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    async def chat(self, messages: list[dict], system: str = "") -> str:
        if self.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_chat(messages, system)
        return await self._ollama_chat(messages, system)

    async def _anthropic_chat(self, messages, system) -> str:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system,
            messages=messages
        )
        return response.content[0].text

    async def _ollama_chat(self, messages, system) -> str:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()["message"]["content"]

    def get_provider_name(self) -> str:
        if self.provider == LLMProvider.ANTHROPIC:
            return f"Claude ({settings.ANTHROPIC_MODEL})"
        return f"Ollama ({settings.OLLAMA_MODEL})"

llm_service = LLMService()

=== backend/services/rag_service.py ===
import chromadb
from chromadb.utils import embedding_functions
from config import settings

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
        ef = embedding_functions.OllamaEmbeddingFunction(
            url=f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            model_name="nomic-embed-text"
        )
        self.collection = self.client.get_or_create_collection(
            name="lenny_transcripts",
            embedding_function=ef
        )

    def retrieve(self, query: str, n_results: int = None) -> list[dict]:
        n = n_results or settings.MAX_CHUNKS_PER_QUERY
        results = self.collection.query(query_texts=[query], n_results=n)
        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            chunks.append({
                "content": doc,
                "source": meta.get("episode_title", "Unknown"),
                "episode_id": meta.get("episode_id", ""),
            })
        return chunks

    def format_context(self, chunks: list[dict]) -> str:
        parts = [f"[Source: {c['source']}]\n{c['content']}" for c in chunks]
        return "\n\n---\n\n".join(parts)

rag_service = RAGService()

=== backend/services/ingest_service.py ===
import httpx

GITHUB_API = "https://api.github.com/repos/ChatPRD/lennys-podcast-transcripts/contents"

async def fetch_transcript_list():
    async with httpx.AsyncClient() as client:
        r = await client.get(GITHUB_API)
        r.raise_for_status()
        return [f for f in r.json() if f["name"].endswith(".md") or f["name"].endswith(".txt")]

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i+chunk_size]))
        i += chunk_size - overlap
    return chunks

async def ingest_transcripts(limit: int = 30):
    from services.rag_service import rag_service
    files = (await fetch_transcript_list())[:limit]
    docs, metas, ids = [], [], []
    async with httpx.AsyncClient() as client:
        for f in files:
            r = await client.get(f["download_url"])
            text = r.text
            title = f["name"].replace(".md","").replace(".txt","").replace("-"," ")
            for idx, chunk in enumerate(chunk_text(text)):
                docs.append(chunk)
                metas.append({"episode_title": title, "episode_id": f["name"], "chunk_index": idx})
                ids.append(f"{f['name']}__chunk_{idx}")
    for i in range(0, len(docs), 100):
        rag_service.collection.upsert(documents=docs[i:i+100], metadatas=metas[i:i+100], ids=ids[i:i+100])
    return {"ingested_files": len(files), "total_chunks": len(docs)}

=== backend/services/essay_service.py ===
SHIP30_SYSTEM = """You are an expert digital writer trained on Ship 30 for 30 principles.
Rules:
1. HOOK: First line must be punchy and contrarian. No fluff opener.
2. LENGTH: Exactly ~1,250 words. Complete standalone essay.
3. STRUCTURE: 3-5 H2 headers forming a clear narrative arc.
4. FORMATTING: Bullets for lists, **bold** for key terms, short paragraphs (2-3 sentences max).
5. SPECIFICITY: Name specific frameworks, numbers, people from transcripts.
6. TAKEAWAY: End with a concrete actionable section.
7. GROUNDING: Every claim cites source as (Source: Episode Name).
8. NO FLUFF: Cut all filler phrases. Every sentence earns its place.
Output pure Markdown only."""

async def generate_essay(question: str, rag_context: str, history: list[dict]) -> str:
    from services.llm_service import llm_service
    user_msg = f"Write a Ship 30 for 30 essay answering:\n\nQUESTION: {question}\n\nTRANSCRIPT KNOWLEDGE BASE:\n{rag_context}\n\nStart with the hook on line 1."
    return await llm_service.chat(messages=[{"role":"user","content":user_msg}], system=SHIP30_SYSTEM)

=== backend/models/schemas.py ===
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

=== backend/db/supabase_client.py ===
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

=== backend/routers/chat.py ===
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

=== backend/routers/sessions.py ===
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

=== backend/routers/artifacts.py ===
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
    context = rag_service.format_context(chunks)
    system = "Generate complete self-contained HTML/CSS. No JS. Return only HTML." if req.artifact_type == "html" else "Generate well-structured Markdown. Return only Markdown."
    content = await llm_service.chat(messages=[{"role":"user","content":f"Context:\n{context}\n\nRequest: {req.prompt}"}], system=system)
    return {"type": req.artifact_type, "content": content, "sources": [c["source"] for c in chunks]}

=== backend/routers/health.py ===
from fastapi import APIRouter
from services.rag_service import rag_service
from services.llm_service import llm_service
from db.supabase_client import supabase

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
def health():
    try:
        count = rag_service.collection.count()
        try: supabase.table("sessions").select("id").limit(1).execute(); db_ok = True
        except: db_ok = False
        return {"status":"ok","provider":llm_service.get_provider_name(),"chroma_docs":count,"db_connected":db_ok}
    except Exception as e:
        return {"status":"degraded","error":str(e)}

=== backend/main.py ===
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, sessions, artifacts, health
import structlog, logging

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO), logger_factory=structlog.PrintLoggerFactory())

app = FastAPI(title="Lenny Growth Assistant API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(artifacts.router)
app.include_router(health.router)

@app.get("/")
def root():
    return {"app": "Lenny Growth Assistant", "status": "running"}

=== backend/ingest/run_ingest.py ===
import asyncio, sys
sys.path.insert(0, "..")
from services.ingest_service import ingest_transcripts

async def main():
    print("Ingesting 30 transcripts...")
    result = await ingest_transcripts(limit=30)
    print(f"Done: {result}")

asyncio.run(main())

=== backend/tests/test_chat.py ===
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health/")
    assert r.status_code == 200

def test_chat_returns_session():
    r = client.post("/api/chat/", json={"message":"What is product-market fit?","mode":"chat"})
    assert r.status_code == 200
    assert "session_id" in r.json()

def test_essay_returns_artifact():
    r = client.post("/api/chat/", json={"message":"How do you build a growth loop?","mode":"essay"})
    data = r.json()
    assert data.get("artifact") is not None

=== backend/requirements.txt ===
fastapi==0.111.0
uvicorn[standard]==0.30.0
anthropic==0.28.0
chromadb==0.5.3
httpx==0.27.0
supabase==2.5.0
pydantic-settings==2.3.0
structlog==24.2.0
python-dotenv==1.0.1
pytest==8.2.2
pytest-asyncio==0.23.7

=== backend/Dockerfile ===
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

=== docker-compose.yml ===
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./backend/chroma_db:/app/chroma_db
    depends_on:
      - ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
volumes:
  ollama_data:

=== .env.example ===
LLM_PROVIDER=ollama
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
ANTHROPIC_MODEL=claude-sonnet-4-6
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
CHROMA_PERSIST_PATH=./chroma_db
MAX_CHUNKS_PER_QUERY=5
MAX_SESSION_HISTORY=10

=== frontend/src/api/client.js ===
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function sendMessage({ message, session_id, mode }) {
  const res = await fetch(`${BASE}/api/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id, mode })
  })
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Failed") }
  return res.json()
}

export async function listSessions() {
  const res = await fetch(`${BASE}/api/sessions/`)
  return res.json()
}

export async function createSession(title = "New Chat") {
  const res = await fetch(`${BASE}/api/sessions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title })
  })
  return res.json()
}

=== frontend/src/components/ModelBadge.jsx ===
export default function ModelBadge({ provider }) {
  if (!provider) return null
  const isLocal = provider.toLowerCase().includes("ollama")
  return (
    
      {isLocal ? "🖥️" : "☁️"} {provider}
    
  )
}

=== frontend/src/components/ArtifactViewer.jsx ===
import ReactMarkdown from "react-markdown"
import { useState } from "react"

export default function ArtifactViewer({ artifact, onClose }) {
  const [view, setView] = useState("preview")
  const isHTML = artifact.type === "html"
  return (
    


      


        


          {artifact.type.toUpperCase()}
          {["preview","source"].map(v => (
             setView(v)} className={`text-xs px-2 py-0.5 rounded ${view===v?"bg-gray-700 text-white":"text-gray-400 hover:text-white"}`}>{v.charAt(0).toUpperCase()+v.slice(1)}
          ))}
        


        


           navigator.clipboard.writeText(artifact.content)} className="text-xs text-gray-400 hover:text-white">Copy
          ✕
        


      


      


        {view === "source" ? (
          

{artifact.content}


        ) : isHTML ? (
          
        ) : (
          <div className="prose prose-invert prose-sm max-w-none"><ReactMarkdown>{artifact.content}</ReactMarkdown></div>
        )}
      </div>
    </div>
  )
}

=== frontend/src/components/MessageBubble.jsx ===
import ReactMarkdown from "react-markdown"

export default function MessageBubble({ message }) {
  const isUser = message.role === "user"
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"}`}>
        <div className="prose prose-invert prose-sm max-w-none"><ReactMarkdown>{message.content}</ReactMarkdown></div>
        {message.sources?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <p className="text-xs text-gray-400">Sources: {message.sources.join(", ")}</p>
          </div>
        )}
      </div>
    </div>
  )
}

=== frontend/src/components/SessionSidebar.jsx ===
export default function SessionSidebar({ sessions, activeSession, onSelect, onNew }) {
  return (
    <div className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-3 border-b border-gray-800">
        <button onClick={onNew} className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm py-2 rounded-lg">+ New Chat</button>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {sessions.map(s => (
          <button key={s.id || s.session_id} onClick={() => onSelect(s.id || s.session_id)}
            className={`w-full text-left px-3 py-2 text-sm truncate hover:bg-gray-800 ${activeSession === (s.id || s.session_id) ? "bg-gray-800 text-white" : "text-gray-400"}`}>
            {s.title || "New Chat"}
          </button>
        ))}
      </div>
    </div>
  )
}

=== frontend/src/components/ChatPane.jsx ===
import { useState, useRef, useEffect } from "react"
import MessageBubble from "./MessageBubble"
import ModelBadge from "./ModelBadge"
import { sendMessage } from "../api/client"

const MODES = [{id:"chat",label:"💬 Chat"},{id:"essay",label:"✍️ Essay"},{id:"artifact",label:"📄 Artifact"}]

export default function ChatPane({ sessionId, setSessionId, setArtifact }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [mode, setMode] = useState("chat")
  const [loading, setLoading] = useState(false)
  const [provider, setProvider] = useState("")
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const text = input
    setMessages(p => [...p, { role: "user", content: text }])
    setInput("")
    setLoading(true)
    try {
      const res = await sendMessage({ message: text, session_id: sessionId, mode })
      if (!sessionId) setSessionId(res.session_id)
      setProvider(res.provider)
      setMessages(p => [...p, { role: "assistant", content: res.message, sources: res.sources }])
      if (res.artifact) setArtifact(res.artifact)
    } catch (e) {
      setMessages(p => [...p, { role: "assistant", content: "Error: " + e.message, sources: [] }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <h1 className="font-semibold text-sm">🎙️ Lenny Growth Assistant</h1>
        <ModelBadge provider={provider} />
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20 text-sm">Ask anything about product growth, retention, or GTM — grounded in Lenny's Podcast.</div>
        )}
        {messages.map((m, i) => <MessageBubble key={i} message={m} />)}
        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full" />
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="px-4 py-3 border-t border-gray-800 space-y-2">
        <div className="flex gap-2">
          {MODES.map(m => (
            <button key={m.id} onClick={() => setMode(m.id)}
              className={`text-xs px-3 py-1 rounded-full ${mode===m.id?"bg-blue-600 text-white":"bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
              {m.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==="Enter" && !e.shiftKey && send()}
            placeholder={mode==="essay"?"Ask a question — get a Ship 30 essay...":"Ask about product growth, retention, GTM..."}
            className="flex-1 bg-gray-800 text-gray-100 text-sm rounded-lg px-4 py-2 outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-500" />
          <button onClick={send} disabled={loading} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg">Send</button>
        </div>
      </div>
    </div>
  )
}

=== frontend/src/App.jsx ===
import { useState, useEffect } from "react"
import ChatPane from "./components/ChatPane"
import ArtifactViewer from "./components/ArtifactViewer"
import SessionSidebar from "./components/SessionSidebar"
import { listSessions } from "./api/client"

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [artifact, setArtifact] = useState(null)
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {})
  }, [sessionId])

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      <SessionSidebar sessions={sessions} activeSession={sessionId} onSelect={setSessionId} onNew={() => setSessionId(null)} />
      <div className="flex flex-1 overflow-hidden">
        <ChatPane sessionId={sessionId} setSessionId={setSessionId} setArtifact={setArtifact} />
        {artifact && <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />}
      </div>
    </div>
  )
}

=== frontend/package.json ===
{
  "name": "lenny-growth-assistant",
  "version": "1.0.0",
  "scripts": { "dev": "vite", "build": "vite build" },
  "dependencies": { "react": "^18.3.0", "react-dom": "^18.3.0", "react-markdown": "^9.0.1" },
  "devDependencies": { "</body>@vitejs/plugin-react": "^4.3.0", "autoprefixer": "^10.4.20", "postcss": "^8.4.41", "tailwindcss": "^3.4.10", "vite": "^5.4.0" }
}

=== frontend/vite.config.js ===
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
export default defineConfig({ plugins: [react()] })

=== frontend/index.html ===
<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1.0" /><title>Lenny Growth Assistant</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>
</html>

Create ALL of these files exactly as written. Do not modify any logic. Do not add extra files. Just create this exact structure.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
