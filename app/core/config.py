from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    DIRECT_URL: str

    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    ENVIRONMENT: str = "development"


settings = Settings()  # type: ignore
