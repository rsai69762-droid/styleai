from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stylai:stylai_dev_password@localhost:5434/stylai"
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    llm_provider: str = "anthropic"  # "anthropic" or "ollama"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
