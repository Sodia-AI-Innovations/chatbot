import logging

from app.models.document import SearchResult
from app.models.response import ChatAnswer, Source
from app.prompts.rag_prompt import NOT_FOUND_MESSAGE, build_prompt
from app.services.llm_service import BaseLLMService, get_llm_service
from app.services.retrieval_service import RetrievalService


logger = logging.getLogger(__name__)

class RagService:
    def __init__(self,
                retriever: RetrievalService| None = None,
                llm: BaseLLMService | None = None,
    ):
        self._retriever = retriever or RetrievalService()
        self._llm = llm or get_llm_service()

    def ask(
            self,
            question: str,
            tenant_id: str | None = None,
            document_ids: list[str] | None =None,
    )-> ChatAnswer:
        question = question.strip()

        results = self._retriever.retrieve(
            question, tenant_id=tenant_id, document_ids=document_ids
        )
        if not results:
            logger.info("No relevant chunks found; LLM call skipped")
            return ChatAnswer(answer=NOT_FOUND_MESSAGE, sources=[])

        system_prompt, user_prompt = build_prompt(question, [r.chunk.text for r in results])
        llm_result = self._llm.generate(system_prompt, user_prompt)

        if NOT_FOUND_MESSAGE in llm_result.text:
            logger.info("Model reported the answer is not in the context")
            return ChatAnswer(answer=NOT_FOUND_MESSAGE, sources=[])
        return ChatAnswer(answer=llm_result.text, sources=self._build_sources(results))


    @staticmethod
    def _build_sources(results: list[SearchResult]) -> list[Source]:
        seen: dict[tuple, Source] = {}
        for r in results: 
            key = (r.chunk.document_id, r.chunk.page_number)
            if key not in seen:
                seen[key] = Source(
                    document_id=r.chunk.document_id,
                    filename=r.chunk.filename,
                    page=r.chunk.page_number,
                    chunk_id=r.chunk.chunk_id,
                    score=round(r.score, 3),
                )
        return list(seen.values())   

    SNIPPET_CHARS = 200
    @classmethod
    def _snippet(cls, text:str) -> str:
        text = " ".join(text.split())
        if len(text) <= cls.SNIPPET_CHARS:
            return text
        return text[: cls.SNIPPET_CHARS].rstrip() + "..."

    @classmethod
    def _build_sources(cls, results: list[SearchResult]) -> list[Source]:
        seen: dict[tuple, Source] = {}
        for r in results:
            c = r.chunk
            key = (c.document_id, c.page_number) if c.page_number is not None else (c.document_id, c.chunk_id)
            if key not in seen:
                seen[key] = Source(
                    document_id=c.document_id,
                    filename=c.filename,
                    page=c.page_number,
                    chunk_id=c.chunk_id,
                    score=round(r.score, 3),
                    snippet=cls._snippet(c.text),
                )
        return list(seen.values())   