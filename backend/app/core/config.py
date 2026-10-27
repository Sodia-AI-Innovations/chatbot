from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",  extra="ignore")

    app_name: str = "rag-chatbot"
    env:str = "dev"
    log_level: str = "INFO"

    llm_provider: str =""
    llm_api_key: str =""
    llm_model: str =""
    llm_max_tokens: int =300

    embedding_provider: str =""
    embedding_model: str =""
    embedding_api_key: str =""
    embedding_dimension: int = 768
    vector_store_backend: str = "pgarray"
    vector_db_url: str =""

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 4
    similarity_threshold: float = 0.6

    max_file_size_mb: int = 10

    allowed_extensions: str = "pdf,docx,txt"
    upload_dir: str = "storage/uploads"
    cors_origins: str = "http://localhost:5173"

    default_tenant_id: str = "default"
    max_question_length: int = 1000

    llm_reasoning_effort: str  = ""
    llm_thinking_budget: int | None = None
    @property
    def allowed_ext_list(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

@lru_cache
def get_settings() -> Settings:
    return Settings()    
