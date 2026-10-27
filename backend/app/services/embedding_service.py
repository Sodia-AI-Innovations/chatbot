import logging
from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import EmbeddingError

logger = logging.getLogger(__name__)

class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed many text (used at ingestion time)."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed one question (used at search time)."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Length af the vectors this services produces.""" 

class landChainEmbeddingService(BaseEmbeddingService):
    def __init__(self, embeddings):
        self._embeddings = embeddings
        self._dimension: int | None = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return[]
        try:
            vectors = self._embeddings.embed_documents(texts)
        except Exception as e:
            logger.error("Embedding failed: %s", type(e).__name__)
            raise EmbeddingError() from e
        logger.info("Embedded %d texts", len(texts))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        try:
            return self._embeddings.embed_query(text)
        except Exception as e:
            logging.error("query embedding failed: %s", type(e).__name__)
            raise EmbeddingError() from e

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._dimension = len(self.embed_query("dimension probe"))
        return self._dimension

def _build_embeddings(provider: str, model:str, api_key: str, dimension: int):
    if provider == "local":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=model or "sentence-transformers/all-MiniLM-L6-v2"
        )
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model= model or "gemini-embedding-001",
            google_api_key = api_key,
            output_dimensionality=dimension,
        )
    raise ValueError(f"Unknown embedding provider: '{provider}'") 

@lru_cache
def get_embedding_service() -> BaseEmbeddingService:
    s = get_settings()
    embeddings =_build_embeddings(
        s.embedding_provider.lower(),
        s.embedding_model,
        s.embedding_api_key,
        s.embedding_dimension,
    )
    return landChainEmbeddingService(embeddings)             
                     