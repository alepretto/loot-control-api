from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://localhost/loot_control"
    DIRECT_URL: str = "postgresql+asyncpg://localhost/loot_control"

    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    ENVIRONMENT: str = "development"
    DB_ECHO: bool = False
    # Comma-separated list of allowed CORS origins, e.g.:
    # ALLOWED_ORIGINS=https://app.lootcontrol.com,https://lootcontrol.com
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://loot-control.com.br"

    COINGECKO_API_KEY: str = ""  # Demo key (gratuito) em coingecko.com — melhora rate limits
    OPENROUTER_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    MINI_APP_URL: str = ""        # e.g. https://loot-control.com.br/mini
    WEBHOOK_URL: str = ""         # e.g. https://loot-control-api.fly.dev (no trailing slash)


settings = Settings()  # type: ignore
