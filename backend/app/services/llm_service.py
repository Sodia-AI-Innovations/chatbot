import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.errors import LLMError

logger = logging.getLogger(__name__)

@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int

class BaseLLMService(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt:str) -> LLMResult:
        """Send a prompt to the model and return its answer plus token uasge."""

class LangChainLLMService(BaseLLMService):
    def __init__(self, chat_model):
        self._chat_model = chat_model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        try:
            response = self._chat_model.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
        except Exception as e:
            logger.error("LLM request failed: %s", type(e).__name__)
            raise LLMError() from e

        text = (response.text or "").strip()
        usage = response.usage_metadata or {}
        result = LLMResult(
            text=text,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
        logger.info(
            "LLM request completed: %d input / %d output tokens",
            result. input_tokens, result.output_tokens,
        )

        if not text:
            logger.warning("LLM returned an empty answuer (output budget used up by thinking?)")
            raise LLMError("the model return as empty answer .")
        return result

def _build_chat_model(provider:str, model:str, api_key: str, max_tokens:int,reasoning_effort:str, thinking_budget:int | None):
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI  

        extra = {}
        if reasoning_effort:
            extra["reasoning_effort"] = reasoning_effort
        if thinking_budget is not None:
            extra["thinking_bugdet"] = thinking_budget

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            max_output_tokens=max_tokens,
            **extra,
        )
    raise ValueError(f"Unknown LLM provider: '{provider}'")

@lru_cache
def get_llm_service() -> BaseLLMService:
    s= get_settings()
    chat_model = _build_chat_model(
        s.llm_provider.lower(), s.llm_model, s.llm_api_key, s.llm_max_tokens,
        s.llm_reasoning_effort, s.llm_thinking_budget,
    )
    return LangChainLLMService(chat_model)
