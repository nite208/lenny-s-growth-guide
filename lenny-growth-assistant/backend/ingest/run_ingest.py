import asyncio, sys
sys.path.insert(0, "..")
from services.ingest_service import ingest_transcripts

async def main():
    print("Ingesting 30 transcripts...")
    result = await ingest_transcripts(limit=30)
    print(f"Done: {result}")

asyncio.run(main())
