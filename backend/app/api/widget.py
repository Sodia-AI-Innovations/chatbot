from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_rag_service
from app.core.db import get_db
from app.core.errors import DomainNotAllowedError, InvalidTokenError
from app.models.bot_token import BotToken
from app.services.rag_service import RagService
from app.utils.domains import normalize_domain

router = APIRouter(tags=["widget"])

class WidgetChatRequest(BaseModel):
    token: str
    question: str

def resolve_token(
        body: WidgetChatRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> BotToken:
        bt = db.query(BotToken).filter_by(token=body.token, is_active=True).first()
        if not bt:
             raise InvalidTokenError()

        if normalize_domain(request.headers.get("origin", "")) != bt.domain:
             raise DomainNotAllowedError()
        return bt

@router.post("/chat")
def widget_chat(
    body: WidgetChatRequest,
    bt: BotToken = Depends(resolve_token),
    rag: RagService = Depends(get_rag_service),
):
    return rag.ask(body.question, tenant_id=str(bt.id), document_ids=None)