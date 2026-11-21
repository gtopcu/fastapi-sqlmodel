from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "FastAPI SQLModel Company & Employee API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "fastapi_db"
    DATABASE_URL: str | None = None

    @computed_field
    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # If standard postgresql:// URL is provided, ensure psycopg v3 dialect is used
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+psycopg://", 1
                )
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
