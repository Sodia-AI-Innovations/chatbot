import logging

from app.core.config import get_settings
from app.core.errors import InvalidQuestionError
from app.models.document import SearchResult
from app.services.embedding_service import BaseEmbeddingService, get_embedding_service
from app.services.vector_store import BaseVectorStore, get_vector_store

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(
            self,
            embedding_service: BaseEmbeddingService | None = None,
            vector_store: BaseVectorStore | None = None,
            top_k: int | None = None,
            similarity_threshold: float | None = None,
    ):
        settings = get_settings()
        self._settings = settings
        self._embedder = embedding_service or get_embedding_service()
        self._store = vector_store or get_vector_store()
        self.top_k = settings.top_k if top_k is None else top_k
        self.similarity_threshold = (
            settings.similarity_threshold if similarity_threshold is None else similarity_threshold
        )
    def retrieve(
            self,
            question: str,
            tenant_id: str | None = None,
            document_ids: list[str] | None = None,
            top_k: int | None = None,
            similarity_threshold: float | None = None,
    ) -> list[SearchResult]:
        question = (question or "").strip()
        if not question or len(question) > self._settings.max_question_length:
            raise InvalidQuestionError()

        tenant_id = tenant_id or self._settings.default_tenant_id
        k = self.top_k if top_k is None else top_k
        threshold = self.similarity_threshold if similarity_threshold is None else similarity_threshold

        query_vector = self._embedder.embed_query(question)
        results = self._store.search(
            query_vector,
            top_k=k,
            tenant_id= tenant_id,
            document_ids=document_ids,
            min_score=threshold
        )
        logger.info(
            "Retrieval executed: %d chunks above threshold %.2f (top_k=%d)",
            len(results), threshold, k,
        )
        return results