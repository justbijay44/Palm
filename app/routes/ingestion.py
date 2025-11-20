from fastapi import APIRouter
from app.models import DocumentIn, DocumentOut

router = APIRouter()

@router.post('/', response_model=DocumentOut)
def doc_ingestion(doc: DocumentIn):
    chunks = [doc.content[i:i+50] for i in range(0, len(doc.content), 50)]
    return DocumentOut(filename=doc.filename, chunks=chunks)