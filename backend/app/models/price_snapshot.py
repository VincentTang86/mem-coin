from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, BigInteger, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pool_address: Mapped[str] = mapped_column(
        String(64), ForeignKey("pools.pool_address", ondelete="CASCADE"), index=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    price_usd: Mapped[float | None] = mapped_column(Numeric(32, 12))
    liquidity_usd: Mapped[float | None] = mapped_column(Numeric(24, 6))
    volume_5m: Mapped[float | None] = mapped_column(Numeric(24, 6))

    __table_args__ = (Index("ix_snap_pool_ts", "pool_address", "ts"),)
