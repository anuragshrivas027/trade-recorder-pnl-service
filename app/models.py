
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    __table_args__ = (
        UniqueConstraint(
            "venue",
            "trade_id",
            name="uq_trade_venue_trade_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    venue: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    trade_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    side: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LatestPrice(Base):
    __tablename__ = "latest_prices"

    symbol: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
