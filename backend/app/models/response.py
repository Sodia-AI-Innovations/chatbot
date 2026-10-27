from pydantic import BaseModel
from datetime import datetime

class Source(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    chunk_id: str |None = None
    score: float | None = None
    snippet: str | None = None

class ChatAnswer(BaseModel):
    answer: str
    sources: list[Source] = [] 

class DocumentInfo(BaseModel) :
    document_id: str
    filename: str
    file_type: str
    size_bytes: int
    page_count: int | None = None
    chunk_count: int
    status: str
    uploaded_at: datetime     