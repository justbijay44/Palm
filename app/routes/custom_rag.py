from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class QueryIn(BaseModel):
    query: str

class QueryOut(BaseModel):
    answer: str

@router.post('/', response_model=QueryIn)
def custom_rag(query: QueryIn):
    answer = f"Response to '{query.query}'"
    return QueryOut(answer=answer)