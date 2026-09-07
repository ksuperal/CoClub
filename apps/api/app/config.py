from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"

    openai_api_key: str
    openai_image_model: str = "gpt-image-2"

    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str | None = None

    ayrshare_api_key: str | None = None

    database_url: str | None = None

    @property
    def ayrshare_enabled(self) -> bool:
        return bool(self.ayrshare_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
