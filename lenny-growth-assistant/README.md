# The Lenny Growth Assistant

RAG-powered product & growth assistant grounded in Lenny's Podcast transcripts.

## Stack
- **Backend**: FastAPI, ChromaDB (RAG), Anthropic or Ollama LLM, Supabase (sessions/messages)
- **Frontend**: React 18 + Vite + Tailwind, Markdown/HTML artifact viewer

## Setup

```bash
cp .env.example .env   # fill in keys
docker compose up --build
```

Ingest transcripts (from `backend/`):

```bash
python ingest/run_ingest.py
```

Frontend:

```bash
cd frontend && npm install && npm run dev
```

## API
- `POST /api/chat/` — chat / essay / artifact modes
- `POST /api/sessions/`, `GET /api/sessions/`, `GET /api/sessions/{id}/messages`
- `POST /api/artifacts/`
- `GET /api/health/`

## Tests

```bash
cd backend && pytest
```
