from functools import lru_cache

from app.core.config import get_settings
from app.services.document_service import DocumentService
from app.services.rag_service import RagService


def get_tenant_id() -> str:
    """ INTEGRATION POINT : replace with real authentication (token, seddion...)
    that returns the id of the logged-in customer. Everthing downstream is
    already scoped by this value."""
    return get_settings().default_tenant_id

@lru_cache
def get_rag_service() -> RagService:
    return RagService()

@lru_cache
def get_document_service() -> DocumentService:
    return DocumentService()

