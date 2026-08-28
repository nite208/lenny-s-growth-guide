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
