import asyncio
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Document, Chunk

async def check_database():
    async with AsyncSessionLocal() as session:
        # Check documents
        result = await session.execute(select(Document))
        documents = result.scalars().all()
        
        print("\n📄 Documents in Database:")
        for doc in documents:
            print(f"  ID: {doc.id}, Filename: {doc.filename}, Chunks: {doc.total_chunks}")
        
        # Check chunks for first document
        if documents:
            doc_id = documents[0].id
            result = await session.execute(
                select(Chunk).where(Chunk.doc_id == doc_id).limit(3)
            )
            chunks = result.scalars().all()
            
            print(f"\n📦 First 3 Chunks for Document {doc_id}:")
            for chunk in chunks:
                print(f"  Chunk {chunk.chunk_index}: {chunk.text[:100]}...")
                print(f"  Vector ID: {chunk.vector_id}")

if __name__ == "__main__":
    asyncio.run(check_database())