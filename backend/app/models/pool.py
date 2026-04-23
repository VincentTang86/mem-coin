from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Pool(Base):
    __tablename__ = "pools"

    pool_address: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_mint: Mapped[str] = mapped_column(
        String(64), ForeignKey("tokens.mint", ondelete="CASCADE"), index=True
    )
    dex: Mapped[str] = mapped_column(String(32), index=True)  # pumpfun_bonding / raydium_amm / raydium_clmm
    quote_mint: Mapped[str | None] = mapped_column(String(64))
    liquidity_usd: Mapped[float | None] = mapped_column(Numeric(24, 6), index=True)
    price_usd: Mapped[float | None] = mapped_column(Numeric(32, 12))
    price_sol: Mapped[float | None] = mapped_column(Numeric(32, 12))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
