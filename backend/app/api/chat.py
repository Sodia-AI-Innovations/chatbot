from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_rag_service, get_tenant_id
from app.core.db import get_db
from app.models.chat import ChatRequest
from app.models.response import ChatAnswer
from app.services.rag_service import RagService
from app.services.usage import log_usage

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatAnswer)
def chat(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    rag: RagService = Depends(get_rag_service),
    db: Session = Depends(get_db),
):
    return rag.ask(request.question, tenant_id=tenant_id, document_ids=request.document_ids)
    log_usage(db, str(bt.id), None, "chat", result.input_tokens, result.output_tokens)
    return result
