from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://memcoin:memcoin@localhost:5432/memcoin"
    sync_database_url: str = "postgresql+psycopg://memcoin:memcoin@localhost:5432/memcoin"
    redis_url: str = "redis://localhost:6379/0"

    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    helius_api_key: str = ""

    pumpfun_api_base: str = "https://frontend-api-v3.pump.fun"
    raydium_api_base: str = "https://api-v3.raydium.io"
    jupiter_price_api: str = "https://lite-api.jup.ag/price/v2"

    discover_interval_seconds: int = 60
    refresh_interval_seconds: int = 30
    max_age_hours: int = 72
    min_liquidity_usd: float = 10000.0

    log_level: str = "INFO"
    http_proxy: str | None = None  # e.g. http://127.0.0.1:7890

    enable_pumpfun: bool = True
    enable_raydium_discover: bool = False  # needs Helius key or it will 429


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
