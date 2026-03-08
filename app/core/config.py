from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://localhost/loot_control"
    DIRECT_URL: str = "postgresql+asyncpg://localhost/loot_control"

    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    ENVIRONMENT: str = "development"
    DB_ECHO: bool = False


settings = Settings()  # type: ignore
