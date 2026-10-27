from fastapi import APIRouter, Depends

from app.api.deps import get_rag_service, get_tenant_id
from app.models.chat import ChatRequest
from app.models.response import ChatAnswer
from app.services.rag_service import RagService

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatAnswer)
def chat(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    rag: RagService = Depends(get_rag_service),
):
    return rag.ask(request.question, tenant_id=tenant_id, document_ids=request.document_ids)