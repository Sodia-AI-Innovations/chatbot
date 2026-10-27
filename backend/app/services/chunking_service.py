import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import get_settings
from app.core.errors import EmptyDocumentError
from app.loaders.base import PageContent
from app.models.document import Chunk
from app.utils.text_cleaner import clean_text

logger = logging.getLogger(__name__)

class ChunkingService:
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        settings = get_settings()
        self.chunk_size = settings.chunk_size if chunk_size is None else chunk_size
        self.chunk_overlap = settings.chunk_overlap if chunk_overlap is None else chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )      
    def chunk_pages(self, pages: list[PageContent], document_id: str, filename: str) -> list[Chunk]:
        chunks: list[Chunk] = []
        index = 0

        for page in pages:
            text = clean_text(page.text)
            if not text:
                continue

            for piece in self._splitter.split_text(text):
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        filename=filename,
                        chunk_id=f"{document_id}_{index}",
                        chunk_index=index,
                        page_number=page.page_number,
                        text=piece,
                    )
                )
                index +=1

        if not chunks:
            raise EmptyDocumentError()

        logger.info("Created %d chunks for document %s", len(chunks), document_id)
        return chunks        