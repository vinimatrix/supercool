from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = {
        "env_prefix": "SUPERCOOL_",
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }

    database_url: str = "postgresql+asyncpg://supercool:supercool@localhost:5432/supercool"
    database_url_sync: str = "postgresql://supercool:supercool@localhost:5432/supercool"
    redis_url: str = "redis://localhost:6379/0"
    nle_url: str = "http://localhost:3001"
    google_api_key: str = ""
    openai_api_key: str = ""
    nvidia_api_key: str = ""
    llm_provider: str = "google"
    llm_fallback_enabled: bool = True
    clip_threshold_dialogue: float = 0.78
    clip_threshold_action: float = 0.70
    local_models_enabled: bool = True
    qwen_backend: str = "auto"  # auto|ollama|llama_cpp


settings = Settings()
