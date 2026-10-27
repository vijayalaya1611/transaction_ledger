import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Transaction Ledger API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./ledger.db",
        description="Database connection URI"
    )
    
    CORS_ORIGINS: str = "*"

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

