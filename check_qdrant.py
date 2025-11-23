import asyncio
from app.services.vector_store import QdrantStore

async def check_qdrant():
    store = QdrantStore(url="http://localhost:6333")
    
    # Get collection info
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://localhost:6333")
    
    try:
        collection_info = client.get_collection("documents")
        print(f"\n🔍 Qdrant Collection Info:")
        print(f"  Collection: documents")
        print(f"  Vectors count: {collection_info.points_count}")
        print(f"  Vector size: {collection_info.config.params.vectors.size}")
        
        # Try a dummy search using the store's method
        dummy_vector = [0.1] * 384
        results = await store.query_vectors("documents", dummy_vector, top_k=3)
        
        print(f"\n🔎 Sample Query Results (top 3):")
        for r in results:
            print(f"  Score: {r['score']:.4f}")
            print(f"  Doc ID: {r['metadata'].get('doc_id')}")
            print(f"  Chunk: {r['metadata'].get('chunk_index')}")
            print(f"  Text: {r['metadata'].get('text', 'N/A')[:80]}...")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_qdrant())