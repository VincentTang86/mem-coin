from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class SolanaRpc:
    def __init__(self, url: str | None = None):
        base = url or settings.solana_rpc_url
        if settings.helius_api_key and "helius" not in base:
            base = f"https://mainnet.helius-rpc.com/?api-key={settings.helius_api_key}"
        self.url = base
        self._client = httpx.AsyncClient(timeout=15.0, proxy=settings.http_proxy)

    async def close(self) -> None:
        await self._client.aclose()

    async def _call(self, method: str, params: list) -> dict:
        r = await self._client.post(
            self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        )
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise RuntimeError(body["error"])
        return body["result"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=8))
    async def first_seen(self, address: str, max_pages: int = 3) -> datetime | None:
        """Return the block_time of the earliest signature for this address.

        Paginates backwards with `before` until the history ends, or `max_pages` is hit.
        If we run out of pages without reaching the beginning, returns None — the
        address has too much history to be a recent meme, don't trust the estimate.

        Each page = 1000 sigs. 3 pages ≈ 3000 sigs ≈ enough to cover the first days
        of a meme launch, but not a stablecoin.
        """
        before: str | None = None
        earliest_block_time: int | None = None
        for _ in range(max_pages):
            params: dict = {"limit": 1000}
            if before is not None:
                params["before"] = before
            sigs = await self._call("getSignaturesForAddress", [address, params])
            if not sigs:
                break
            for s in sigs:
                bt = s.get("blockTime")
                if bt is not None and (earliest_block_time is None or bt < earliest_block_time):
                    earliest_block_time = bt
            if len(sigs) < 1000:
                # history ended on this page — earliest is truly the earliest
                if earliest_block_time is None:
                    return None
                return datetime.fromtimestamp(earliest_block_time, tz=timezone.utc)
            before = sigs[-1]["signature"]
        # max_pages exhausted without reaching the end → too much history, skip
        return None
