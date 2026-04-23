from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from app.config import settings


@dataclass
class FilterCriteria:
    max_age_hours: int = settings.max_age_hours
    min_liquidity_usd: float = settings.min_liquidity_usd
    dex: str | None = None  # optional filter


def matches(
    launched_at: datetime | None,
    liquidity_usd: float | None,
    dex: str | None = None,
    criteria: FilterCriteria | None = None,
    now: datetime | None = None,
) -> bool:
    c = criteria or FilterCriteria()
    if launched_at is None or liquidity_usd is None:
        return False
    now = now or datetime.now(timezone.utc)
    if launched_at.tzinfo is None:
        launched_at = launched_at.replace(tzinfo=timezone.utc)
    age = now - launched_at
    if age < timedelta(0) or age > timedelta(hours=c.max_age_hours):
        return False
    if float(liquidity_usd) <= c.min_liquidity_usd:
        return False
    if c.dex and dex != c.dex:
        return False
    return True
