from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    document_ids: list[str] | None = None
