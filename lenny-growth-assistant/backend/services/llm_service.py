import anthropic
import httpx
from config import settings, LLMProvider
import structlog

log = structlog.get_logger()


class LLMServiceError(Exception):
    def __init__(self, code: str, user_message: str):
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._validate_startup_config()

    def _validate_startup_config(self):
        if self.provider != LLMProvider.ANTHROPIC:
            return
        if not settings.ANTHROPIC_API_KEY:
            log.warning(
                "anthropic_startup_config_invalid",
                reason="missing_api_key",
                provider=self.provider.value,
            )
            raise RuntimeError("Anthropic API key is required when LLM_PROVIDER=anthropic")
        if not settings.ANTHROPIC_API_KEY.startswith("sk-"):
            log.warning(
                "anthropic_startup_config_invalid",
                reason="invalid_api_key_format",
                provider=self.provider.value,
            )
            raise RuntimeError("Anthropic API key format is invalid")

    async def chat(self, messages: list[dict], system: str = "") -> str:
        if self.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_chat(messages, system)
        return await self._ollama_chat(messages, system)

    async def _anthropic_chat(self, messages, system) -> str:
        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system,
                messages=messages
            )
            return response.content[0].text
        except Exception as exc:
            log.error("anthropic_request_failed", error=str(exc))
            raise LLMServiceError(
                "anthropic_unavailable",
                "Cloud model unavailable — check Anthropic API key and connectivity.",
            ) from exc

    async def _ollama_chat(self, messages, system) -> str:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()["message"]["content"]
        except httpx.RequestError as exc:
            log.error("ollama_unreachable", error=str(exc), base_url=settings.OLLAMA_BASE_URL)
            raise LLMServiceError(
                "ollama_unreachable",
                "Local model unavailable — check Ollama is running",
            ) from exc
        except httpx.HTTPStatusError as exc:
            log.error("ollama_http_error", error=str(exc))
            raise LLMServiceError(
                "ollama_http_error",
                "Local model unavailable — check Ollama is running",
            ) from exc

    async def is_provider_connected(self) -> bool:
        if self.provider == LLMProvider.ANTHROPIC:
            return bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.startswith("sk-"))
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                r.raise_for_status()
            return True
        except Exception:
            return False

    def get_provider_name(self) -> str:
        if self.provider == LLMProvider.ANTHROPIC:
            return f"Claude ({settings.ANTHROPIC_MODEL})"
        return f"Ollama ({settings.OLLAMA_MODEL})"

llm_service = LLMService()
