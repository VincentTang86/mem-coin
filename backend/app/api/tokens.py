from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Pool, PriceSnapshot, Token
from app.schemas import TokenListResponse, TokenOut

router = APIRouter(prefix="/api/tokens", tags=["tokens"])

# effective launched_at: use true launched_at if known, else first_seen_at
EFFECTIVE_LAUNCHED = func.coalesce(Token.launched_at, Token.first_seen_at)

SORT_FIELDS = {
    "liquidity_usd": Pool.liquidity_usd,
    "launched_at": EFFECTIVE_LAUNCHED,
    "price_usd": Pool.price_usd,
}


def _age_hours(launched_at: datetime | None) -> float | None:
    if not launched_at:
        return None
    if launched_at.tzinfo is None:
        launched_at = launched_at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - launched_at).total_seconds() / 3600.0


@router.get("", response_model=TokenListResponse)
async def list_tokens(
    max_age_hours: int = Query(72, ge=1, le=24 * 30),
    min_liquidity_usd: float = Query(10000.0, ge=0),
    dex: str | None = Query(None),
    sort: str = Query("liquidity_usd"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    if sort not in SORT_FIELDS:
        raise HTTPException(400, f"invalid sort field: {sort}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    # pick the best pool per token: max liquidity
    best_pool_sq = (
        select(
            Pool.token_mint,
            func.max(Pool.liquidity_usd).label("best_liq"),
        )
        .group_by(Pool.token_mint)
        .subquery()
    )

    q = (
        select(Token, Pool)
        .join(best_pool_sq, best_pool_sq.c.token_mint == Token.mint)
        .join(
            Pool,
            (Pool.token_mint == Token.mint) & (Pool.liquidity_usd == best_pool_sq.c.best_liq),
        )
        .where(EFFECTIVE_LAUNCHED >= cutoff)
        .where(Pool.liquidity_usd > min_liquidity_usd)
    )
    if dex:
        q = q.where(Pool.dex == dex)

    order_col = SORT_FIELDS[sort]
    q = q.order_by(desc(order_col) if order == "desc" else asc(order_col))

    total = (await session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

    q = q.limit(page_size).offset((page - 1) * page_size)
    rows = (await session.execute(q)).all()

    items = []
    for (t, p) in rows:
        effective = t.launched_at or t.first_seen_at
        items.append(
            TokenOut(
                mint=t.mint,
                symbol=t.symbol,
                name=t.name,
                source=t.source,
                launched_at=effective,
                metadata_uri=t.metadata_uri,
                best_pool_address=p.pool_address,
                best_dex=p.dex,
                liquidity_usd=float(p.liquidity_usd) if p.liquidity_usd is not None else None,
                price_usd=float(p.price_usd) if p.price_usd is not None else None,
                age_hours=_age_hours(effective),
            )
        )
    return TokenListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{mint}")
async def get_token(mint: str, session: AsyncSession = Depends(get_session)):
    token = await session.get(Token, mint)
    if not token:
        raise HTTPException(404, "token not found")
    pools = (await session.execute(select(Pool).where(Pool.token_mint == mint))).scalars().all()
    snaps = (
        await session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.pool_address.in_([p.pool_address for p in pools] or [""]))
            .order_by(PriceSnapshot.ts.desc())
            .limit(200)
        )
    ).scalars().all()
    return {
        "token": {
            "mint": token.mint,
            "symbol": token.symbol,
            "name": token.name,
            "source": token.source,
            "launched_at": token.launched_at,
            "metadata_uri": token.metadata_uri,
            "age_hours": _age_hours(token.launched_at),
        },
        "pools": [
            {
                "pool_address": p.pool_address,
                "dex": p.dex,
                "quote_mint": p.quote_mint,
                "liquidity_usd": float(p.liquidity_usd) if p.liquidity_usd is not None else None,
                "price_usd": float(p.price_usd) if p.price_usd is not None else None,
                "updated_at": p.updated_at,
            }
            for p in pools
        ],
        "snapshots": [
            {
                "pool_address": s.pool_address,
                "ts": s.ts,
                "price_usd": float(s.price_usd) if s.price_usd is not None else None,
                "liquidity_usd": float(s.liquidity_usd) if s.liquidity_usd is not None else None,
            }
            for s in snaps
        ],
    }
