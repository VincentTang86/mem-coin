import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

SOL_MINT = "So11111111111111111111111111111111111111112"


class PriceOracle:
    """USD price oracle.

    Primary: Raydium `/mint/price` (same host as the rest of the raydium client).
    Optional: Jupiter via JUPITER_PRICE_API if the raydium one breaks.
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10.0, proxy=settings.http_proxy)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def usd_prices(self, mints: list[str]) -> dict[str, float]:
        if not mints:
            return {}
        url = f"{settings.raydium_api_base.rstrip('/')}/mint/price"
        r = await self._client.get(url, params={"mints": ",".join(mints)})
        r.raise_for_status()
        body = r.json() or {}
        data = body.get("data") or {}
        out: dict[str, float] = {}
        for m, v in data.items():
            if v is None:
                continue
            try:
                out[m] = float(v)
            except (TypeError, ValueError):
                continue
        return out

    async def sol_usd(self) -> float | None:
        prices = await self.usd_prices([SOL_MINT])
        return prices.get(SOL_MINT)
