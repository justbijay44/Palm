import uuid
from pathlib import Path
from typing import Tuple, List
from PyPDF2 import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, Chunk
from app.services.embeddings import get_embeddings
from app.services.vector_store import QdrantStore
from app.helper import chunk_fixed, chunk_semantic

UPLOADED_DIR = Path('uploads')
UPLOADED_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "documents"
VECTOR_SIZE = 384    # all-MiniLM-L6-v2 produces 384-dim vectors

# so with vector_store we can switch between different vector db
# like a langchain
vector_store = QdrantStore(url="http://localhost:6333")

async def save_file(file_content: bytes, filename: str) -> Tuple[Path, str]:
    """
    Save uploaded file & return (path, saved_filename)
    """
    suffix = Path(filename).suffix.lower()
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = UPLOADED_DIR / saved_name

    with saved_path.open('wb') as f:
        f.write(file_content)
    
    return saved_path, saved_name

async def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from pdf or txt files
    """
    suffix = file_path.suffix.lower()

    if suffix == '.txt':
        return file_path.read_text(encoding='utf-8')
    elif suffix == '.pdf':
        reader = PdfReader(str(file_path))
        return "\n".join([page.extract_text() or '' for page in reader.pages])
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    
async def chunk_text(text: str, strategy: str, chunk_size: int) -> List[str]:
    """
    Chunk text using a strategy
    """
    if strategy == "fixed":
        return chunk_fixed(text, chunk_size=chunk_size)
    elif strategy == "semantic":
        return chunk_semantic(text, chunk_size=chunk_size)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    
async def ingestion_pipeline(
        file_content:str,
        filename:str,
        chunk_strategy:str,
        chunk_size:int,
        session: AsyncSession
)   -> Tuple[int, str, int]:
    """
    - Complete Ingestion Pipeline
    - Returns (document_id, filename, total_chunks)
    """

    saved_path, saved_name = await save_file(file_content, filename)

    try:
        # Extract Text
        text = await extract_text_from_file(saved_path)

        # Chunk Text
        chunks = await chunk_text(text, chunk_strategy, chunk_size)

        if not chunks:
            raise ValueError("No Chunks were generated from the document.")

        # Embedding Chunk
        embeddings = await get_embeddings(chunks)

        # Ensure Qdrant Collection
        await vector_store.ensure_collection(COLLECTION_NAME, VECTOR_SIZE)

        # Create doc in db
        doc = Document(
            filename = filename,
            total_chunks = len(chunks)
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        # Prepare Metadata
        metadatas = [
            {
                "doc_id": doc.id,
                "chunk_index": i,
                "text": chunk[:500]    # preview
            } for i, chunk in enumerate(chunks)
        ]

        vector_ids = [f"doc{doc.id}_chunk{i}" for i in range(len(chunks))]

        # Store Embedding in Qdrant
        await vector_store.upsert_vectors(
            namespace=COLLECTION_NAME,
            ids=vector_ids,
            vectors=embeddings,
            metadatas=metadatas
        )

        # Save Chunk in db
        for i, chunk_content in enumerate(chunks):
            chunk_obj = Chunk(
                doc_id = doc.id,
                chunk_index = i,
                text = chunk_content,
                vector_id=vector_ids[i]
            )
            session.add(chunk_obj)
        
        await session.commit()

        return doc.id, filename, len(chunks)
    
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise e