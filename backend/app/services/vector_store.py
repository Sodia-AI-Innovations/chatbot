import logging
from abc import ABC, abstractmethod
from functools import lru_cache

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from app.core.config import get_settings
from app.core.errors import VectorStoreError
from app.models.document import Chunk, SearchResult
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

class BaseVectorStore(ABC):
    @abstractmethod
    def setup(self) -> None:
        """Create tables/indexes if they don't exist."""

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]], tenant_id: str) -> None:
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        tenant_id: str,
        document_ids: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        ...

    @abstractmethod
    def delete_document(self, document_id: str, tenant_id: str) -> int:
        """Delete all chunks of a document. Return how many were removed."""

class pgVectorStore(BaseVectorStore):
    def __init__(self, db_url: str, dimension: int):
        # SQLAlchemy-style URLs contain "+psycopg"; plain psycopg doesn't accept that
        self._url = db_url.replace("postgresql+psycopg://", "postgresql://")
        self._dimension = int(dimension)

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._url)
        register_vector(conn)
        return conn
    def setup(self) -> None:
        try:
            # The extension must exist before register_vector() can run
            with psycopg.connect(self._url) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            with self._connect() as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id     TEXT PRIMARY KEY,
                        document_id  TEXT NOT NULL,
                        tenant_id    TEXT NOT NULL,
                        filename     TEXT NOT NULL,
                        chunk_index  INT NOT NULL,
                        page_number  INT,
                        text         TEXT NOT NULL,
                        embedding    vector({self._dimension}) NOT NULL
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
                    "ON chunks USING hnsw (embedding vector_cosine_ops)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS chunks_tenant_doc_idx "
                    "ON chunks (tenant_id, document_id)"
                )
        except psycopg.Error as e:
            logger.error("Vector store setup failed: %s", type(e).__name__)
            raise VectorStoreError() from e
    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]], tenant_id: str) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        rows = [
            (c.chunk_id, c.document_id, tenant_id, c.filename,
             c.chunk_index, c.page_number, c.text, np.array(e))
            for c, e in zip(chunks, embeddings)
        ]
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO chunks (chunk_id, document_id, tenant_id, filename, "
                        "chunk_index, page_number, text, embedding) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        rows,
                    )
        except psycopg.Error as e:
            logger.error("Storing chunks failed: %s", type(e).__name__)
            raise VectorStoreError() from e
        logger.info("Stored %d chunks", len(rows))
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        tenant_id: str,
        document_ids: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        q = np.array(query_embedding)

        sql = (
            "SELECT chunk_id, document_id, filename, chunk_index, page_number, text, "
            "1 - (embedding <=> %s) AS score "
            "FROM chunks WHERE tenant_id = %s"
        )
        params: list = [q, tenant_id]

        if document_ids:
            sql += " AND document_id = ANY(%s)"
            params.append(document_ids)

        sql += " ORDER BY embedding <=> %s LIMIT %s"
        params += [q, top_k]

        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        except psycopg.Error as e:
            logger.error("Vector search failed: %s", type(e).__name__)
            raise VectorStoreError() from e

        results = [
            SearchResult(
                chunk=Chunk(
                    document_id=r[1], filename=r[2], chunk_id=r[0],
                    chunk_index=r[3], page_number=r[4], text=r[5],
                ),
                score=float(r[6]),
            )
            for r in rows
        ]
        results = [r for r in results if r.score >= min_score]
        logger.info("Search returned %d chunks (top_k=%d)", len(results), top_k)
        return results

    def delete_document(self, document_id: str, tenant_id: str) -> int:
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "DELETE FROM chunks WHERE document_id = %s AND tenant_id = %s",
                    (document_id, tenant_id),
                )
                deleted = cur.rowcount
        except psycopg.Error as e:
            logger.error("Delete failed: %s", type(e).__name__)
            raise VectorStoreError() from e
        logger.info("Deleted %d chunks for document %s", deleted, document_id)
        return deleted           

class PgArrayVectorStore(BaseVectorStore):
    """Plain Postgres, no pgvector extension. Vectors are stored as float arrays
    and similarity is computed in Python. Fine for prototypes; use PgVectorStore at scale."""

    def __init__(self, db_url: str, dimension: int):
        self._url = db_url.replace("postgresql+psycopg://", "postgresql://")
        self._dimension = int(dimension)

    def setup(self) -> None:
        try:
            with psycopg.connect(self._url) as conn:
                conn.execute("""
                     CREATE TABLE IF NOT EXISTS chunks_array (
                        chunk_id     TEXT PRIMARY KEY,
                        document_id  TEXT NOT NULL,
                        tenant_id    TEXT NOT NULL,
                        filename     TEXT NOT NULL,
                        chunk_index  INT NOT NULL,
                        page_number  INT,
                        text         TEXT NOT NULL,
                        embedding    DOUBLE PRECISION[] NOT NULL
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS chunks_array_tenant_doc_idx "
                    "ON chunks_array (tenant_id, document_id)"
                )
        except psycopg.Error as e:
            logger.error("Vector store setup failed: %s", type(e).__name__)
            raise VectorStoreError() from e
    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]], tenant_id: str) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        rows = [
            (c.chunk_id, c.document_id, tenant_id, c.filename,
             c.chunk_index, c.page_number, c.text, [float(x) for x in e])
             for c, e in zip(chunks, embeddings)
        ]
        try:
            with psycopg.connect(self._url) as conn:
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO chunks_array (chunk_id, document_id, tenant_id, filename, "
                        "chunk_index, page_number, text, embedding) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        rows,
                    )
        except psycopg.Error as e:
            logger.error("Storing chunks failed: %s", type(e).__name__)
            raise VectorStoreError() from e
        logger.info("Stored %d chunks", len(rows)) 
    def search(self, query_embedding: list[float], top_k: int, tenant_id: str, document_ids: list[str] | None = None, min_score: float = 0) -> list[SearchResult]:
        q = np.array(query_embedding, dtype=float)

        where = "tenant_id = %s"
        params: list = [tenant_id]
        if document_ids:
            where += " AND document_id = ANY(%s)"
            params.append(document_ids)

        try:
            with psycopg.connect(self._url) as conn:
                rows = conn.execute(
                    f"SELECT chunk_id, embedding FROM chunks_array WHERE {where}", params
                ).fetchall()
                if not rows:
                    return []


                ids = [r[0] for r in rows]
                matrix = np.array([r[1] for r in rows], dtype=float)
                denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
                denom[denom == 0] = 1e-12 
                scores = (matrix @ q) / denom


                best = np.argsort(-scores)[:top_k]
                top = [(ids[i], float(scores[i])) for i in best if scores[i] >= min_score]
                if not top:
                    return []

                details = conn.execute(
                    "SELECT chunk_id, document_id, filename, chunk_index, page_number, text "
                    " FROM chunks_array WHERE chunk_id = ANY(%s)",
                    ([cid for cid, _ in top],),
                ).fetchall()
        except psycopg.Error as e:
            logger.error("Vector search failed: %s ", type(e).__name__)
            raise VectorStoreError() from e

        by_id = {d[0]: d for d in details}
        results = []
        for cid, score in top:
            d = by_id[cid]
            results.append(
                SearchResult(
                    chunk=Chunk(
                        document_id=d[1], filename=d[2], chunk_id=d[0],
                        chunk_index=d[3], page_number=d[4], text=d[5],
                    ),
                    score=score,
                )
            )
        logger.info("Search returned %d chunks (top_k=%d)", len(results), top_k)
        return results
    def delete_document(self, document_id: str, tenant_id: str) -> int:
        try:
            with psycopg.connect(self._url) as conn:
                cur = conn.execute(
                    "DELETE FROM chunks_array WHERE  document_id = %s AND tenant_id = %s",
                    (document_id, tenant_id),
                )
                deleted = cur.rowcount
        except psycopg.Error as e:
            logger.error("Delete failed: %s", type(e).__name__)
            raise VectorStoreError() from e
        logger.info("Deleted %d chunks for document %s", deleted, document_id)
        return deleted   
@lru_cache
def get_vector_store() -> BaseVectorStore:
    settings = get_settings()
    dimension = get_embedding_service().dimension
    backend = settings.vector_store_backend.lower()
    if backend == "pgvector":
        store = pgVectorStore(settings.vector_db_url,dimension)
    elif backend == "pgarray":
        store = PgArrayVectorStore(settings.vector_db_url, dimension)
    else:
        raise ValueError(f"Unknown vector store backend: '{backend}'")        
    store.setup()
    return store                        

            