def chunk_fixed(text: str, chunk_size: int = 500) -> list[str]:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def chunk_semantic(text: str, chunk_size: int = 500) -> list[str]:
    paragraph = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraph:
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk += (" " if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size):
                    chunks.append(para[i:i+chunk_size])
                current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)
    return chunks
