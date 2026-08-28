from pydantic_settings import BaseSettings
from enum import Enum

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class Settings(BaseSettings):
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    ANTHROPIC_API_KEY: str = ""
    FRONTEND_URL: str = ""
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
