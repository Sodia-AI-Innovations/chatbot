import logging
import os
import uuid
from contextlib import suppress
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.errors import DocumentNotFoundError
from app.loaders.registry import get_loader
from app.models.response import DocumentInfo
from app.services.chunking_service import ChunkingService
from app.services.document_repository import BaseDocumentRepository, get_document_repository
from app.services.embedding_service import BaseEmbeddingService, get_embedding_service
from app.services.vector_store import BaseVectorStore, get_vector_store
from app.utils.file_validation import validate_file

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(
            self,
            repository: BaseDocumentRepository | None = None,
            chunker: ChunkingService | None =None,
            embedder: BaseEmbeddingService | None =None,
            store: BaseVectorStore | None = None,
        ):
            self._settings = get_settings()
            self._repository = repository or get_document_repository()
            self._chunker = chunker or ChunkingService()
            self._embedder = embedder or get_embedding_service()
            self._store = store or get_vector_store()

    def ingest(self, filename:str, content: bytes, tenant_id: str | None = None) -> DocumentInfo:
          tenant_id = tenant_id or self._settings.default_tenant_id
          filename = os.path.basename(filename or "")[:255]
          extension = validate_file(filename, len(content))

          document_id = uuid.uuid4().hex
          logger.info("Documentuploaded: id=%s type=%s size=%d bytes", document_id, extension, len(content))

          os.makedirs(self._settings.upload_dir, exist_ok=True)
          path = os.path.join(self._settings.upload_dir, f"{document_id}.{extension}")

          try:
                with open(path, "wb") as f:
                      f.write(content)

                logger.info("Document processing started: id=%s", document_id)
                pages = get_loader(extension).load(path)
                chunks = self._chunker.chunk_pages(pages, document_id, filename)
                vectors = self._embedder.embed_documents([c.text for c in chunks])

                try:
                      self._store.add_chunks(chunks, vectors, tenant_id)
                      info =DocumentInfo(
                            document_id=document_id,
                            filename=filename,
                            file_type=extension,
                            size_bytes=len(content),
                            page_count=len(pages) if extension == "pdf" else None,
                            chunk_count=len(chunks),
                            status="processed",
                            uploaded_at=datetime.now(timezone.utc),
                      )
                      self._repository.add(tenant_id, info)
                except Exception:
                      with suppress(Exception):
                            self._store.delete_document(document_id, tenant_id)
                      raise 
          finally:               
               with suppress(OSError):
                    os.remove(path)

          logger.info("Document processing compllted: id=%s chunks=%d", document_id, len(chunks))
          return info
              
    def list_documents(self, tenant_id: str | None =None)-> list[DocumentInfo]:
         return self._repository.list_all(tenant_id or self._settings.default_tenant_id)
    def delete_document(self, document_id: str, tenant_id: str | None = None) -> None:
         tenant_id = tenant_id or self._settings.default_tenant_id
         if self._repository.get(document_id, tenant_id) is None:
              raise DocumentNotFoundError()

         removed =self._store.delete_document(document_id, tenant_id)
         self._repository.delete(document_id, tenant_id)
         logger.info("Document deleted: id=%s chunks_removes=%d", document_id, removed)
            
        