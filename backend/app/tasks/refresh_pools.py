import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update

from app.config import settings
from app.db import SessionLocal
from app.models import Pool, PriceSnapshot, Token
from app.services.pumpfun_client import PumpFunClient
from app.services.raydium_client import RaydiumClient
from app.services.price_oracle import PriceOracle
from app.services.filter_engine import matches
from app.tasks.celery_app import celery_app
from app.tasks.publisher import publish_hit

log = logging.getLogger(__name__)


async def _refresh() -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=settings.max_age_hours)
    updated = 0
    hits = 0

    pump = PumpFunClient()
    ray = RaydiumClient()
    oracle = PriceOracle()

    try:
        try:
            sol_usd = await oracle.sol_usd() or 0.0
        except Exception as e:
            log.warning("sol_usd fetch failed: %s", e)
            sol_usd = 0.0

        async with SessionLocal() as session:
            rows = (
                await session.execute(
                    select(Pool, Token)
                    .join(Token, Token.mint == Pool.token_mint)
                    .where(Token.launched_at.is_not(None))
                    .where(Token.launched_at >= cutoff)
                )
            ).all()

            # group pools by dex
            pump_pools = [(p, t) for (p, t) in rows if p.dex == "pumpfun_bonding"]
            ray_pools = [(p, t) for (p, t) in rows if p.dex.startswith("raydium")]

            # refresh pump.fun pools via coin endpoint
            for p, t in pump_pools:
                try:
                    coin = await pump.get_coin(t.mint)
                except Exception as e:
                    log.warning("pump get_coin %s failed: %s", t.mint, e)
                    continue
                if not coin:
                    continue
                liq = (coin.virtual_sol_reserves or 0) / 1e9 * sol_usd
                price_sol = None
                if coin.virtual_token_reserves:
                    price_sol = (coin.virtual_sol_reserves or 0) / (coin.virtual_token_reserves or 1)
                price_usd = (price_sol or 0) * sol_usd if price_sol else None

                await session.execute(
                    update(Pool)
                    .where(Pool.pool_address == p.pool_address)
                    .values(liquidity_usd=liq, price_usd=price_usd, price_sol=price_sol, updated_at=now)
                )
                session.add(PriceSnapshot(pool_address=p.pool_address, price_usd=price_usd, liquidity_usd=liq))
                updated += 1

                if matches(t.launched_at, liq, dex=p.dex, now=now):
                    hits += 1
                    await publish_hit({
                        "mint": t.mint, "symbol": t.symbol, "name": t.name,
                        "dex": p.dex, "liquidity_usd": liq, "price_usd": price_usd,
                        "launched_at": t.launched_at.isoformat() if t.launched_at else None,
                    })

            # refresh raydium pools — batch by mint (API returns pool list per mint)
            for p, t in ray_pools:
                try:
                    fresh = await ray.pools_by_mint(t.mint)
                except Exception as e:
                    log.warning("raydium pools_by_mint %s failed: %s", t.mint, e)
                    continue
                match = next((fp for fp in fresh if fp.pool_address == p.pool_address), None)
                if not match:
                    continue
                liq = match.tvl
                price_usd = match.price
                await session.execute(
                    update(Pool)
                    .where(Pool.pool_address == p.pool_address)
                    .values(liquidity_usd=liq, price_usd=price_usd, updated_at=now)
                )
                session.add(PriceSnapshot(pool_address=p.pool_address, price_usd=price_usd, liquidity_usd=liq))
                updated += 1

                if matches(t.launched_at, liq, dex=p.dex, now=now):
                    hits += 1
                    await publish_hit({
                        "mint": t.mint, "symbol": t.symbol, "name": t.name,
                        "dex": p.dex, "liquidity_usd": liq, "price_usd": price_usd,
                        "launched_at": t.launched_at.isoformat() if t.launched_at else None,
                    })

            await session.commit()
    finally:
        await pump.close()
        await ray.close()
        await oracle.close()

    log.info("refresh_pools: updated=%s hits=%s", updated, hits)
    return {"updated": updated, "hits": hits}


@celery_app.task(name="app.tasks.refresh_pools.run")
def run() -> dict:
    try:
        return asyncio.run(_refresh())
    except Exception as e:
        log.exception("refresh_pools failed: %s", e)
        return {"updated": 0, "hits": 0, "error": str(e)}
