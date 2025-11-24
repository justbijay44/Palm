from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.services.rag.rag_pipeline import RAGPipeline

router = APIRouter()

rag_pipeline = RAGPipeline()

class QueryRequest(BaseModel):
    query: str = Field(..., description="User's Question")
    session_id: str = Field(..., description="Users unique identifier")
    top_k: int = Field(5, description="Top 5 relvant chunk")

class QueryRespond(BaseModel):
    answer: str
    sources: List[Dict]
    session_id: str

@router.post('/query', response_model=QueryRespond)
async def query_document(request: QueryRequest):
    """
    - Retrive relavant chunks
    - Use redis for conversation history
    - Generate answer with llm
    """

    try:
        answer, source = await rag_pipeline.query(
            user_query= request.query,
            session_id= request.session_id,
            top_k= request.top_k
        )

        return QueryRespond(
            answer=answer,
            sources=source,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query Failed: {str(e)}")
    
@router.delete("session/{session_id}")
async def clear_session(session_id: str):
    """ Clear the chat history for a session. """
    try:
        await rag_pipeline.redis_service.clear_session(session_id)
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))