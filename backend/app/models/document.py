from dataclasses import dataclass

@dataclass
class Chunk:
    document_id: str
    filename: str
    chunk_id: str
    chunk_index: int
    page_number: int | None
    text: str

@dataclass
class SearchResult:
    chunk: Chunk
    score: float    