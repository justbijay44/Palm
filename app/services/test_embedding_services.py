import asyncio
from app.services.embeddings import get_embeddings

async def test():
    texts = ["Hello world", "This is a test", "Another document"]
    embeddings = await get_embeddings(texts)

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Each embedding has {len(embeddings[0])} dimensions")
    print(f"First 5 values: {embeddings[0][:5]}")

asyncio.run(test()) 