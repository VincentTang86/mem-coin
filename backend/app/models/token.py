from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Token(Base):
    __tablename__ = "tokens"

    mint: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str | None] = mapped_column(String(128))
    decimals: Mapped[int | None] = mapped_column(Integer)
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    creator: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32), index=True)  # pumpfun / raydium
    metadata_uri: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_tokens_launched_at_desc", launched_at.desc()),)
