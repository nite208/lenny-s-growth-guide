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
