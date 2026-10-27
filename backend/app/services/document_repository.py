import logging
from abc import ABC, abstractmethod
from functools import lru_cache

import psycopg

from app.core.config import get_settings
from app.core.errors import DatabaseError
from app.models.response import DocumentInfo


logger = logging.getLogger(__name__)

_COLUMNS = "document_id, filename, file_type, size_bytes, page_count, chunk_count, status, uploaded_at"

def _to_info(row) -> DocumentInfo:
    return DocumentInfo(
        document_id=row[0], filename=row[1], file_type=row[2], size_bytes=row[3],
        page_count=row[4], chunk_count=row[5] , status=row[6], uploaded_at=row[7],
    )

class BaseDocumentRepository(ABC):
    @abstractmethod
    def setup(self) -> None: ...

    @abstractmethod
    def add(self, tenant_id: str, info: DocumentInfo) -> None: ...

    @abstractmethod
    def list_all(self, tenant_id: str) -> list[DocumentInfo]: ...

    @abstractmethod
    def get(self , document_id: str, tenant_id: str) -> DocumentInfo | None: ...
    @abstractmethod
    def delete(self, document_id:str, tenant_id: str) -> bool: ...

class pgDocumentRepository(BaseDocumentRepository):
    def __init__(self, db_url: str):
        self._url = db_url.replace("postgresql+psycopg://", "postgresql://")

    def setup(self) -> None:
        try:
            with psycopg.connect(self._url) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id   TEXT PRIMARY KEY,
                        tenant_id     TEXT NOT NULL,
                        filename      TEXT NOT NULL,
                        file_type     TEXT NOT NULL,
                        size_bytes    BIGINT NOT NULL,
                        page_count    INT,
                        chunk_count   INT NOT NULL,
                        status        TEXT NOT NULL,
                        uploaded_at   TIMESTAMPTZ NOT NULL
                        )
                    """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS documents_tenant_idx "
                    "On documents (tenant_id, uploaded_at DESC)"
                    )
        except psycopg.Error as e:
            logger.error("Document table setup failed : %s ", type(e).__name__)
            raise DatabaseError() from e
    def add(self, tenant_id: str, info: DocumentInfo) -> None:
        try:
            with psycopg.connect(self._url) as conn:
                conn.execute(
                    f"INSERT INTO documents (tenant_id, {_COLUMNS})"
                    " VALUES(%s, %s, %s, %s, %s, %s , %s, %s ,%s)",
                    (tenant_id, info.document_id, info.filename, info. file_type,
                     info.size_bytes, info.page_count, info.chunk_count,
                     info.status, info.uploaded_at),
                )
        except psycopg.Error as e:
            logger.error("Saving document record failed: %s",  type(e).__name__)
            raise DatabaseError() from e
    def list_all(self, tenant_id: str) -> list[DocumentInfo]:
        try:
            with psycopg.connect(self._url) as conn:
                rows = conn.execute(
                    f"SELECT {_COLUMNS} FROM documents WHERE tenant_id =%s "
                    "ORDER BY uploaded_at DESC",
                    (tenant_id,),
                ).fetchall()
        except psycopg.Error as e:
            logger.error("Listing document failed: %s", type(e).__name__)
            raise DatabaseError() from e 
        return [_to_info(r) for r in rows]
    def get(self, document_id: str, tenant_id: str) -> DocumentInfo | None:
        try:
             with psycopg.connect(self._url)as conn:
                 row = conn.execute(
                     f"SELECT {_COLUMNS} FROM documents WHERE document_id = %s AND tenant_id =%s",
                     (document_id, tenant_id),
                 ).fetchone()
        except psycopg.Error as e:
            logger.error("Fetching documents failed: %s", type(e).__name__)
            raise DatabaseError() from e
        return _to_info(row) if row else None
    def delete(self, document_id: str, tenant_id: str) -> bool:
        try:
            with psycopg.connect(self._url) as conn:
                cur = conn.execute(
                    "DELETE FROM documents WHERE document_id = %s AND tenant_id = %s",
                    (document_id, tenant_id),
                )
                return cur.rowcount > 0
        except psycopg.Error as e:
            logger.error("Deleting document record failed: %s", type(e).__name__)
            raise DatabaseError() from e

@lru_cache
def get_document_repository() -> BaseDocumentRepository:
    repository = pgDocumentRepository(get_settings(). vector_db_url)
    repository.setup()
    return repository             
                    