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
