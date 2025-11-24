from typing import List
import asyncio
from sentence_transformers import SentenceTransformer

# loading the model globally once
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embedding using sentence transformer
    """
    if not isinstance(texts, list):
        raise ValueError(f"Input must be a list of strings, got {type(texts)}")
    
    clean_texts = [str(t) for t in texts if t is not None]

    if len(clean_texts) == 0:
        return []
    
    model = _get_model()
    loop = asyncio.get_running_loop()

    def _encode():
        embeddings = model.encode(clean_texts)
        return [embed.tolist() for embed in embeddings]
    
    # model.encode is cpu heavy and can block event loop
    # run_in_executor runs the heavy one in another thread so it wont block fastapi
    return await loop.run_in_executor(None, _encode)

