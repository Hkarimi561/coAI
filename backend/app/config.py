from functools import lru_cache
from urllib.parse import quote

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # --- Core -------------------------------------------------------------
    app_env: str = "production"
    log_level: str = "INFO"
    # Either set DATABASE_URL directly, or let it be built (URL-encoded) from the POSTGRES_* parts.
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")
    postgres_user: str = "devops"
    postgres_password: str = "devops"
    postgres_db: str = "devops_ai"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "devops_kb"

    # --- Auth -------------------------------------------------------------
    jwt_secret: str = "change-me-in-production-please-use-a-long-random-string"
    jwt_expire_hours: int = 12
    cookie_name: str = "devops_session"
    cookie_secure: bool = False
    admin_email: str | None = None
    admin_password: str | None = None
    admin_name: str = "Administrator"

    # --- Docs store -------------------------------------------------------
    docs_dir: str = "/data/docs"
    auto_index_on_start: bool = True
    chunk_max_chars: int = 1400

    # --- LLM --------------------------------------------------------------
    llm_provider: str = "ollama"  # "ollama" (native /api/chat) | "openai" (OpenAI-compatible /chat/completions)
    llm_base_url: str = "http://host.docker.internal:11434"
    llm_model: str = "qwen3.5:4b"
    llm_api_key: str | None = None
    llm_temperature: float = 0.2
    llm_timeout_s: float = 180.0
    llm_num_ctx: int = 8192
    llm_think: bool = False  # Ollama only: enable "thinking" mode for reasoning models
    llm_grader_enabled: bool = False  # extra LLM call to validate that retrieved context really answers the question

    # --- Embeddings -------------------------------------------------------
    embedding_provider: str = "local"  # "local" (sentence-transformers) | "ollama" | "openai"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None

    # --- Retrieval thresholds --------------------------------------------
    retrieval_top_k: int = 5
    min_context_score: float = 0.72  # below this a chunk is not even shown to the LLM
    doc_sufficiency_score: float = 0.80
    solution_sufficiency_score: float = 0.82
    web_cache_sufficiency_score: float = 0.82

    # --- Chat answer cache ---
    answer_cache_enabled: bool = True
    answer_cache_ttl_hours: int = 24

    # --- Web search -------------------------------------------------------
    websearch_provider: str = "searxng"  # "searxng" | "tavily" | "none"
    searxng_url: str = "http://searxng:8080"
    tavily_api_key: str | None = None
    websearch_max_results: int = 6
    # GitHub project documentation (llms.txt / README / docs/*.md) as a web-research source; also switchable in the admin UI
    github_docs_enabled: bool = True
    github_docs_max_repos: int = 2
    github_docs_max_files: int = 3
    websearch_timeout_s: float = 20.0
    web_cache_ttl_hours: int = 24 * 14
    web_negative_ttl_hours: int = 1
    single_flight_lock_ttl_s: int = 45
    single_flight_wait_s: float = 50.0

    # --- Docker (read-only) ----------------------------------------------
    docker_host: str | None = "http://docker-proxy:2375"
    docker_allowed_containers: str = ""  # comma separated names / glob patterns; empty => feature disabled
    docker_log_tail: int = 120

    # --- CI ---------------------------------------------------------------
    ci_provider: str = "none"  # "none" | "github"
    github_token: str | None = None
    github_repo: str | None = None  # "owner/repo"
    github_api_url: str = "https://api.github.com"
    github_branch: str | None = None

    # --- Rate limits ------------------------------------------------------
    chat_rate_limit_per_minute: int = 20
    login_rate_limit_per_5min: int = 10

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        user, pwd = quote(self.postgres_user, safe=""), quote(self.postgres_password, safe="")
        return f"postgresql+asyncpg://{user}:{pwd}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def docker_allowlist(self) -> list[str]:
        return [p.strip() for p in self.docker_allowed_containers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
