from typing import List, Dict, Tuple
from app.services.shared.embeddings import get_embeddings
from app.services.shared.vector_store import QdrantStore
from app.services.rag.llm_services import LLMServices
from app.services.rag.redis_service import RedisService

COLLECTION_NAME = 'documents'

class RAGPipeline:
    def __init__(self):
        print("🚀 Initializing RAG Pipeline...")
        
        print("  📊 Initializing Vector Store...")
        self.vector_store = QdrantStore(url='http://localhost:6333')
        
        print("  💾 Initializing Redis Service...")
        self.redis_service = RedisService()
        
        print("  🤖 Initializing LLM Service...")
        self.llm_service = LLMServices()
        
        print("✅ RAG Pipeline Ready")

    async def query(self, user_query: str, session_id: str, top_k = 5) -> Tuple[str, List[dict]]:
        """Complete RAG Pipeline"""
        
        print(f"\n{'='*60}")
        print(f"📝 NEW QUERY: {user_query}")
        print(f"🔑 Session ID: {session_id}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Embed query
            print("Step 1/6: 🔢 Generating embeddings...")
            query_embedding = await get_embeddings([user_query])
            print(f"  ✅ Embedding shape: {len(query_embedding[0])}")

            # Step 2: Search Qdrant
            print(f"\nStep 2/6: 🔍 Searching Qdrant (top_k={top_k})...")
            search_result = await self.vector_store.query_vectors(
                namespace=COLLECTION_NAME,
                vector=query_embedding[0],
                top_k=top_k
            )
            print(f"  ✅ Found {len(search_result)} relevant chunks")
            
            # Step 3: Build context
            print("\nStep 3/6: 📚 Building context...")
            context = "Based on the following document excerpts:\n\n"
            sources = []

            for i, result in enumerate(search_result, 1):
                metadata = result['metadata']
                chunk_text = metadata.get('text', '')
                context += f"[{i}] {chunk_text}\n\n"
                
                sources.append({
                    "doc_id": metadata.get('doc_id'),
                    "chunk_index": metadata.get('chunk_index'),
                    "score": result['score']
                })
            print(f"  ✅ Context built with {len(sources)} sources")

            # Step 4: Get chat history
            print(f"\nStep 4/6: 💾 Fetching chat history from Redis...")
            chat_history = await self.redis_service.get_chat_history(session_id)

            # Step 5: Build LLM prompt
            print("\nStep 5/6: 🤖 Preparing LLM prompt...")
            system_prompt = """You are a helpful AI assistant that answers questions based on provided document excerpts.

Rules:
- Answer based ONLY on the provided context
- If the context doesn't contain the answer, say "I don't have enough information to answer that"
- Be concise and clear
- Cite which excerpt number [1], [2], etc. you used"""

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(chat_history)
            messages.append({
                "role": "user",
                "content": f"{context}\n\nQuestion: {user_query}"
            })
            print(f"  ✅ Prompt has {len(messages)} messages")

            # Step 6: Generate response
            print("\nStep 6/6: 🧠 Calling LLM...")
            answer = await self.llm_service.generate_response(messages)
            print(f"  ✅ Got answer: {answer[:100]}...")

            # Step 7: Save to Redis
            print("\n💾 Saving conversation to Redis...")
            await self.redis_service.add_message(
                session_id=session_id,
                message=[
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": answer},
                ]
            )

            print(f"\n✅ QUERY COMPLETED SUCCESSFULLY\n{'='*60}\n")
            return answer, sources
            
        except Exception as e:
            print(f"\n❌ ERROR in RAG Pipeline: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise