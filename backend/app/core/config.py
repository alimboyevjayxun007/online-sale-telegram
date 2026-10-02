from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "production"] = "development"
    app_secret_key: SecretStr = SecretStr("")
    encryption_key: SecretStr = SecretStr("")
    timezone: str = "Asia/Tashkent"
    public_base_url: str = "http://localhost:8000"
    webapp_url: str = "http://localhost:3000"

    bot_token: SecretStr = SecretStr("")
    bot_username: str = ""
    owner_telegram_id: int = 0
    webhook_secret: SecretStr = SecretStr("")
    log_chat_id: int | None = None
    bot_mode: Literal["webhook", "polling"] = "polling"
    throttle_ms: int = 400
    dev_mock_provider: bool = False  # development only: deliver orders with the mock provider

    database_url: str = "postgresql+asyncpg://premium:premium@127.0.0.1:5432/premium"
    redis_url: str = "redis://127.0.0.1:6379/0"

    ton_network: Literal["mainnet", "testnet"] = "mainnet"
    tonapi_key: SecretStr = SecretStr("")
    toncenter_api_key: SecretStr = SecretStr("")
    hot_wallet_version: str = "v5r1"
    hot_wallet_mnemonic_file: str = ""
    admin_ton_address: str = ""
    admin_ton_memo: str = ""

    fragment_mode: Literal["direct", "api"] = "direct"
    fragment_api_key: SecretStr = SecretStr("")
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_for_production(self) -> list[str]:
        """Return the names of required settings that are still empty."""
        required = {
            "APP_SECRET_KEY": self.app_secret_key.get_secret_value(),
            "ENCRYPTION_KEY": self.encryption_key.get_secret_value(),
            "BOT_TOKEN": self.bot_token.get_secret_value(),
            "WEBHOOK_SECRET": self.webhook_secret.get_secret_value(),
            "OWNER_TELEGRAM_ID": self.owner_telegram_id,
            "ADMIN_TON_ADDRESS": self.admin_ton_address,
        }
        if self.dev_mock_provider:
            return ["DEV_MOCK_PROVIDER must be false"]
        return [name for name, value in required.items() if not value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
