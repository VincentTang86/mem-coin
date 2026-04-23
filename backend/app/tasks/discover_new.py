import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.db import SessionLocal
from app.models import Token, Pool
from app.services.pumpfun_client import PumpFunClient
from app.services.raydium_client import RaydiumClient
from app.services.solana_rpc import SolanaRpc
from app.tasks.celery_app import celery_app

log = logging.getLogger(__name__)

SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# Any mint that appears here will be treated as the *quote* side of a pool,
# never as "the meme being monitored". Extend if you see blue-chips leaking in.
QUOTE_MINTS = {
    SOL_MINT, USDC_MINT, USDT_MINT,
    "USDSwr9ApdHk5bvJKMjkff41iTrdcyTRgMEcZQQsTwcA",   # USDS
    "USD1ttGY1N7NvEzkAZxnKS4XBmhXmWc5PzJanHbNeEm",   # USD1
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",   # ETH (Wormhole)
    "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh",   # WBTC (Wormhole)
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",   # stSOL
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",   # JitoSOL
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",    # mSOL
    "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1",    # bSOL
}


async def _discover() -> dict:
    inserted_tokens = 0
    inserted_pools = 0

    pump = PumpFunClient()
    ray = RaydiumClient()
    rpc = SolanaRpc()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)

    try:
        # --- Pump.fun newest coins ---
        coins = []
        if settings.enable_pumpfun:
            try:
                coins = await pump.recent_coins(limit=150)
            except Exception as e:
                log.warning("pumpfun recent_coins failed: %s", e)
        async with SessionLocal() as session:
            for c in coins:
                if c.created_timestamp and c.created_timestamp < cutoff:
                    continue
                stmt = pg_insert(Token).values(
                    mint=c.mint,
                    symbol=c.symbol,
                    name=c.name,
                    decimals=6,
                    launched_at=c.created_timestamp,
                    creator=c.creator,
                    source="pumpfun",
                    metadata_uri=c.metadata_uri,
                ).on_conflict_do_update(
                    index_elements=["mint"],
                    set_={"symbol": c.symbol, "name": c.name, "launched_at": c.created_timestamp},
                )
                r = await session.execute(stmt)
                inserted_tokens += r.rowcount or 0

                if c.bonding_curve:
                    pstmt = pg_insert(Pool).values(
                        pool_address=c.bonding_curve,
                        token_mint=c.mint,
                        dex="pumpfun_bonding",
                        quote_mint=SOL_MINT,
                    ).on_conflict_do_nothing(index_elements=["pool_address"])
                    pr = await session.execute(pstmt)
                    inserted_pools += pr.rowcount or 0
            await session.commit()

        # --- Raydium newest pools ---
        pools = []
        if settings.enable_raydium_discover:
            try:
                pools = await ray.list_new_pools(page=1, page_size=100)
            except Exception as e:
                log.warning("raydium list_new_pools failed: %s", e)
        async with SessionLocal() as session:
            for p in pools:
                # determine which side is the meme token (the non-quote side)
                if p.base_mint in QUOTE_MINTS and p.quote_mint not in QUOTE_MINTS:
                    token_mint = p.quote_mint
                    token_symbol = p.mint_b_symbol
                elif p.quote_mint in QUOTE_MINTS and p.base_mint not in QUOTE_MINTS:
                    token_mint = p.base_mint
                    token_symbol = p.mint_a_symbol
                else:
                    continue  # skip stable-stable / sol-usdc

                # Prefer pool openTime from Raydium (reliable, 1 API call away);
                # fall back to RPC signature-based first_seen (slow + unreliable for
                # high-activity mints).
                launched_at = p.open_time
                if launched_at is None:
                    existing = await session.get(Token, token_mint)
                    launched_at = existing.launched_at if existing else None
                if launched_at is None:
                    try:
                        launched_at = await rpc.first_seen(token_mint)
                    except Exception as e:
                        log.warning("rpc first_seen failed for %s: %s", token_mint, e)
                        launched_at = None

                if launched_at and launched_at < cutoff:
                    continue  # older than 3d, skip
                if launched_at is None:
                    # can't prove it's within 3d (RPC rate-limited or no history); skip
                    continue

                tstmt = pg_insert(Token).values(
                    mint=token_mint,
                    symbol=token_symbol,
                    name=token_symbol,
                    source="raydium",
                    launched_at=launched_at,
                ).on_conflict_do_update(
                    index_elements=["mint"],
                    set_={"launched_at": launched_at, "symbol": token_symbol, "name": token_symbol},
                )
                tr = await session.execute(tstmt)
                inserted_tokens += tr.rowcount or 0

                dex = "raydium_clmm" if p.pool_type.lower().startswith("concentrated") else "raydium_amm"
                pstmt = pg_insert(Pool).values(
                    pool_address=p.pool_address,
                    token_mint=token_mint,
                    dex=dex,
                    quote_mint=p.base_mint if token_mint == p.quote_mint else p.quote_mint,
                    liquidity_usd=p.tvl,
                    price_usd=p.price,
                ).on_conflict_do_update(
                    index_elements=["pool_address"],
                    set_={"liquidity_usd": p.tvl, "price_usd": p.price},
                )
                pr = await session.execute(pstmt)
                inserted_pools += pr.rowcount or 0
            await session.commit()

    finally:
        await pump.close()
        await ray.close()
        await rpc.close()

    log.info("discover_new: tokens=%s pools=%s", inserted_tokens, inserted_pools)
    return {"tokens": inserted_tokens, "pools": inserted_pools}


@celery_app.task(name="app.tasks.discover_new.run")
def run() -> dict:
    try:
        return asyncio.run(_discover())
    except Exception as e:
        log.exception("discover_new failed: %s", e)
        return {"tokens": 0, "pools": 0, "error": str(e)}
