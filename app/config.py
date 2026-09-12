from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SUPERCOOL_"}

    database_url: str = "postgresql+asyncpg://supercool:supercool@localhost:5432/supercool"
    database_url_sync: str = "postgresql://supercool:supercool@localhost:5432/supercool"
    redis_url: str = "redis://localhost:6379/0"
    nle_url: str = "http://localhost:8080"
    google_api_key: str = ""
    openai_api_key: str = ""
    nvidia_api_key: str = ""
    llm_provider: str = "google"
    llm_fallback_enabled: bool = True


settings = Settings()
