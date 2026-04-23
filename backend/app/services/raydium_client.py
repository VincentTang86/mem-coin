from dataclasses import dataclass
from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


@dataclass
class RaydiumPool:
    pool_address: str
    base_mint: str
    quote_mint: str
    pool_type: str  # "Standard" (AMM v4) or "Concentrated" (CLMM)
    price: float | None
    tvl: float | None
    mint_a_symbol: str | None
    mint_b_symbol: str | None
    open_time: datetime | None  # pool open/creation time; proxy for token launch


def _parse_pool(p: dict) -> RaydiumPool:
    mint_a = p.get("mintA") or {}
    mint_b = p.get("mintB") or {}
    ot_raw = p.get("openTime")
    open_time: datetime | None = None
    try:
        ot_int = int(ot_raw) if ot_raw is not None else 0
        if ot_int > 0:
            open_time = datetime.fromtimestamp(ot_int, tz=timezone.utc)
    except (TypeError, ValueError):
        open_time = None
    return RaydiumPool(
        pool_address=p.get("id") or p.get("ammId"),
        base_mint=mint_a.get("address") or p.get("baseMint"),
        quote_mint=mint_b.get("address") or p.get("quoteMint"),
        pool_type=p.get("type", "Standard"),
        price=p.get("price"),
        tvl=p.get("tvl"),
        mint_a_symbol=mint_a.get("symbol"),
        mint_b_symbol=mint_b.get("symbol"),
        open_time=open_time,
    )


class RaydiumClient:
    def __init__(self, base: str | None = None):
        self.base = base or settings.raydium_api_base
        self._client = httpx.AsyncClient(base_url=self.base, timeout=15.0, proxy=settings.http_proxy)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def list_new_pools(self, page: int = 1, page_size: int = 100) -> list[RaydiumPool]:
        """Returns the newest pools across Standard + Concentrated, sorted by creation time desc."""
        r = await self._client.get(
            "/pools/info/list",
            params={
                "poolType": "all",
                "poolSortField": "default",
                "sortType": "desc",
                "pageSize": page_size,
                "page": page,
            },
        )
        r.raise_for_status()
        body = r.json()
        data = (body.get("data") or {}).get("data") or []
        return [_parse_pool(p) for p in data if (p.get("id") or p.get("ammId"))]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def pools_by_mint(self, mint: str) -> list[RaydiumPool]:
        r = await self._client.get(
            "/pools/info/mint",
            params={"mint1": mint, "poolType": "all", "poolSortField": "liquidity", "sortType": "desc", "pageSize": 50, "page": 1},
        )
        r.raise_for_status()
        body = r.json()
        data = (body.get("data") or {}).get("data") or []
        return [_parse_pool(p) for p in data if (p.get("id") or p.get("ammId"))]
