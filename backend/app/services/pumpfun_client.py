from dataclasses import dataclass
from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


@dataclass
class PumpCoin:
    mint: str
    name: str | None
    symbol: str | None
    creator: str | None
    created_timestamp: datetime | None
    bonding_curve: str | None
    virtual_sol_reserves: float | None
    virtual_token_reserves: float | None
    usd_market_cap: float | None
    metadata_uri: str | None
    complete: bool


def _parse(c: dict) -> PumpCoin:
    ts = c.get("created_timestamp")
    if ts is not None:
        # Pump.fun returns ms epoch
        ts = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    return PumpCoin(
        mint=c["mint"],
        name=c.get("name"),
        symbol=c.get("symbol"),
        creator=c.get("creator"),
        created_timestamp=ts,
        bonding_curve=c.get("bonding_curve"),
        virtual_sol_reserves=c.get("virtual_sol_reserves"),
        virtual_token_reserves=c.get("virtual_token_reserves"),
        usd_market_cap=c.get("usd_market_cap"),
        metadata_uri=c.get("image_uri") or c.get("metadata_uri"),
        complete=bool(c.get("complete")),
    )


class PumpFunClient:
    def __init__(self, base: str | None = None):
        self.base = base or settings.pumpfun_api_base
        self._client = httpx.AsyncClient(
            base_url=self.base,
            timeout=15.0,
            headers={"User-Agent": "mem-coin-monitor/0.1"},
            proxy=settings.http_proxy,
        )

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def recent_coins(self, limit: int = 100, offset: int = 0) -> list[PumpCoin]:
        r = await self._client.get(
            "/coins",
            params={"limit": limit, "offset": offset, "sort": "created_timestamp", "order": "DESC"},
        )
        r.raise_for_status()
        data = r.json()
        return [_parse(c) for c in data if c.get("mint")]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def get_coin(self, mint: str) -> PumpCoin | None:
        r = await self._client.get(f"/coins/{mint}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return _parse(r.json())
