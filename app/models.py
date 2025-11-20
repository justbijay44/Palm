from pydantic import BaseModel

class DocumentIn(BaseModel):
    filename: str
    content: str

class DocumentOut(BaseModel):
    filename: str
    chunks: list[str]
