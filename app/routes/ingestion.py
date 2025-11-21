import os
import uuid
from pathlib import Path
from typing import Literal
from PyPDF2 import PdfReader

from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter()

UPLOADED_DIR = Path('uploads')
UPLOADED_DIR.mkdir(parents=True, exist_ok=True)

allowed_file_ext = {'.pdf', '.txt'}
max_file_size = 25 * 1024 * 1024    # 25MB

def _is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in allowed_file_ext

class UploadResponse(BaseModel):
    original_filename: str
    saved_filename: str
    content_type: str
    byte_size: int

async def _save_uploaded_file(uploaded_file: UploadFile, destination: Path) -> int:
    """
    - to save the uploaded file in small chunks
    - reading in small chunks helps to avoid memory crash
    """
    with destination.open('wb') as buffer:
        size = 0
        while True:
            chunk = await uploaded_file.read(1024 * 1024) # 1MB chunk
            if not chunk:
                break
            buffer.write(chunk)
            size += len(chunk)
            if size > max_file_size:
                break
    
    return size

# File Upload
@router.post('/upload', response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    - to handle file uploads & save the files
    """
    # validation
    if not _is_allowed(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension. Allowed: {', '.join(allowed_file_ext)}",
        )
    
    suffix = Path(file.filename).suffix.lower()
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = UPLOADED_DIR / saved_name

    try:
        size = await _save_uploaded_file(file, saved_path)
        if size > max_file_size:
            try:
                saved_path.unlink(missing_ok=True)  # to delete without raising error
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail = f'file size too large. Limit is {max_file_size} bytes.'
            )
        
        # reset file pointer for future use
        await file.seek(0)

        return UploadResponse(
            original_filename= file.filename,
            saved_filename= str(saved_path),
            content_type= file.content_type or "application/octet-stream",
            byte_size= size,
        )
    except HTTPException:
        raise
    except Exception as e:
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f'Failed to store uploaded file: {e}'
        )
    
# File Extraction
EXTRACT_MAX_PREVIEW = 400 # preview of extracted text

@router.get('/extraction/{saved_filename}', response_class=JSONResponse)
async def extract_text(saved_filename: str):
    """
    extract text from previous saved files
    """
    file_path = Path(saved_filename)
    if not file_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content= {'error': 'File not found at {file_path}.'}
        )
    
    suffix = file_path.suffix.lower()

    try:
        if suffix == '.txt':
            text = file_path.read_text(encoding='utf-8')
        elif suffix == '.pdf':
            reader = PdfReader(str(file_path))
            text = "\n".join([page.extract_text() or '' for page in reader.pages])
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content= {'error': "Unsupported file type."}
            )
        
        preview = text[:EXTRACT_MAX_PREVIEW]
        return {
            "saved_filename": saved_filename,
            "length": len(text),
            "preview": preview,
            "full_text": text
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract text: {str(e)}"}
        )
    
# Chunking
from app.helper import chunk_fixed, chunk_semantic

class ChunkRequest(BaseModel):
    saved_filename: str = Field(..., description= "Filename returned from upload"),
    chunk_strat: Literal["fixed", "semantic"] = Field("fixed", description= "Chunking Strategy"),
    chunk_size: int = Field(500, description="Chunk Size"),

@router.post('/chunks')
async def chunk_document(request: ChunkRequest):
    file_path = Path(request.saved_filename)
    if not file_path.exists():
        return HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"File not found: {request.saved_filename}"
        )
    
    suffix = file_path.suffix.lower()
    try:
        if suffix == '.txt':
            text = file_path.read_text(encoding='utf-8')
        elif suffix == '.pdf':
            reader = PdfReader(str(file_path))
            text = "\n".join([page.extract_text() or '' for page in reader.pages])
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content= {'error': "Unsupported file type."}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read the file {e}")
    
    if request.chunk_strat == "fixed":
        chunks = chunk_fixed(text, chunk_size= request.chunk_size)
    else:
        chunks = chunk_semantic(text, chunk_size= request.chunk_size)

    return {
        "saved_filename": request.saved_filename,
        "strategy": request.chunk_strat,
        "total_chunks": len(chunks),
        "preview": chunks[:3],
        "chunks": chunks,
    }