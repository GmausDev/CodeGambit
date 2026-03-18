from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    ANTHROPIC_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./codegambit.db"
    SANDBOX_IMAGE: str = "codegambit-sandbox:latest"
    SANDBOX_TIMEOUT: int = 30
    SANDBOX_MEMORY_LIMIT: str = "256m"
    SANDBOX_CPU_LIMIT: float = 0.5
    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "info"


settings = Settings()
