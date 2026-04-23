from datetime import datetime
from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    mint: str
    symbol: str | None = None
    name: str | None = None
    source: str
    launched_at: datetime | None = None
    metadata_uri: str | None = None
    best_pool_address: str | None = None
    best_dex: str | None = None
    liquidity_usd: float | None = None
    price_usd: float | None = None
    age_hours: float | None = None


class TokenListResponse(BaseModel):
    items: list[TokenOut]
    total: int
    page: int
    page_size: int


class SavedFilterIn(BaseModel):
    name: str
    payload: dict
    client_id: str | None = None


class SavedFilterOut(BaseModel):
    id: int
    name: str
    payload: dict
    client_id: str | None = None
    created_at: datetime
