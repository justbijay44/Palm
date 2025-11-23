"""
Qdrant is a vector db used to store embedding as points.
Each point is 384vectors which are in VectorParams
With Cosine Distance the Qdrant can decide which points are similar

"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import asyncio
from typing import List

# abstract base
class VectorStore:
    async def ensure_collection(self, collection_name: str, vector_size: int):
        raise NotImplementedError() # means not implemented yet and to make it overriden later
    
    async def upsert_vectors(self, namespace: str, ids: List[str], vectors: List[List[float]], metadatas: List[dict]):
        raise NotImplementedError()
    
    async def query_vectors(self, namespace: str, vector: List[float], top_k: int = 5) -> List[dict]:
        raise NotImplementedError()

# implementation
class QdrantStore(VectorStore):
    def __init__(self, url: str='http://localhost:6333'):
        self.client = QdrantClient(url= url)   # local qdrant

    async def ensure_collection(self, collection_name: str, vector_size: int):
        """Create collection if doesn't exist"""
        loop = asyncio.get_running_loop()
        def _sync():
            try:
                self.client.get_collection(collection_name)
                print(f"Collection '{collection_name}' already exists")
            except Exception:
                from qdrant_client.models import Distance, VectorParams
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"Created collection '{collection_name}' with vector size {vector_size}")
        await loop.run_in_executor(None, _sync)
    
    async def upsert_vectors(self, namespace, ids, vectors, metadatas):
        """
         - for insert or update
         - safely handles in case of re-ingestion
        """
        loop = asyncio.get_running_loop()
        def _sync():
            from qdrant_client.models import PointStruct
            points = [
                PointStruct(id=hash(id_str) % (2**63), vector=v, payload=m)  
                for id_str, v, m in zip(ids, vectors, metadatas)
            ]
            self.client.upsert(collection_name=namespace, points=points)
            print(f"Upserted {len(points)} vectors to '{namespace}'")
        await loop.run_in_executor(None, _sync)

    async def query_vectors(self, namespace, vector, top_k=5):
        """
            for RAG chat
        """        
        loop = asyncio.get_running_loop()
        def _sync():
            from qdrant_client.models import NamedVector
            resp = self.client.query_points(
                collection_name=namespace,
                query=vector,
                limit=top_k
            )
            return [
                {"id": point.id, "score": point.score, "metadata": point.payload} 
                for point in resp.points
            ]
        return await loop.run_in_executor(None, _sync)