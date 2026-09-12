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

    database_url: str | None = None

    # Direct social posting (Step 4) — Meta covers both Facebook Page and Instagram
    # posting via one OAuth grant; TikTok is separate. All optional so the app still
    # runs end-to-end without them (posts fall back to "pending_credentials"), except
    # the encryption key, which is required the moment any token needs to be stored.
    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str | None = None
    meta_graph_version: str = "v25.0"
    # Facebook Login for Business requires a saved "Login Configuration" (created in the
    # app dashboard under Facebook Login for Business > Configurations) — the OAuth dialog
    # is invoked with this config_id instead of a raw scope list. Without one, the app
    # shows as "not active" on the OAuth dialog even with everything else set up correctly.
    meta_login_config_id: str | None = None

    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None
    tiktok_redirect_uri: str | None = None

    social_token_encryption_key: str = ""

    frontend_url: str = "http://localhost:3000"

    # Video generation (Step 2, video variants) — image-to-video via Luma's Ray
    # model (Luma Agents API, platform.lumalabs.ai). Optional, same "gated, not
    # broken, if unconfigured" pattern as the OAuth settings above: without a key,
    # video generation is unavailable with a clear error rather than a crash.
    luma_api_key: str | None = None
    luma_base_url: str = "https://agents.lumalabs.ai/v1"

    @property
    def meta_oauth_enabled(self) -> bool:
        return bool(
            self.meta_app_id and self.meta_app_secret and self.meta_redirect_uri and self.meta_login_config_id
        )

    @property
    def tiktok_oauth_enabled(self) -> bool:
        return bool(self.tiktok_client_key and self.tiktok_client_secret and self.tiktok_redirect_uri)

    @property
    def luma_enabled(self) -> bool:
        return bool(self.luma_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
