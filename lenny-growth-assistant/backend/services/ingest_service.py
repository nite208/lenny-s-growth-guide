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
