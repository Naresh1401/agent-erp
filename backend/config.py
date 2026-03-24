"""AgentERP – Configuration via pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me"
    frontend_url: str = "http://localhost:3000"

    # ── Postgres ──
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agent_erp"
    postgres_user: str = "erp_admin"
    postgres_password: str = "change-me-in-production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Qdrant ──
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "erp_documents"

    # ── Redis ──
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ── LLM ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # ── Observability ──
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agent-erp"
    wandb_api_key: str = ""
    wandb_project: str = "agent-erp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
