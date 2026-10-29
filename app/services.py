
from datetime import timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import LatestPrice, Trade
from app.schemas import TradeCreate


class TradeConflict(Exception):
    """Raised when a trade conflicts with existing data or position rules."""


def _normalize_timestamp(value):
    """Treat timezone-naive timestamps as UTC for consistent comparison."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)



def _same_trade(existing: Trade, payload: TradeCreate) -> bool:
    """Compare trade details without false timestamp mismatches."""
    return (
        existing.venue == payload.venue
        and existing.trade_id == payload.trade_id
        and existing.symbol == payload.symbol
        and existing.side == payload.side
        and existing.quantity == payload.quantity
        and existing.price == payload.price
        and _normalize_timestamp(existing.timestamp).replace(
            microsecond=0
        )
        == _normalize_timestamp(payload.timestamp).replace(
            microsecond=0
        )
    )



def _find_existing_trade(
    db: Session,
    venue: str,
    trade_id: str,
) -> Trade | None:
    """Find a trade using its venue and trade ID."""
    return db.scalar(
        select(Trade).where(
            Trade.venue == venue,
            Trade.trade_id == trade_id,
        )
    )


def record_trade(db: Session, payload: TradeCreate) -> tuple[Trade, bool]:
    """
    Record a trade exactly once.

    Returns (trade, True) for a new trade.
    Returns (trade, False) for an identical duplicate.

    Raises TradeConflict for conflicting duplicate IDs or overselling.
    """

    try:
        # PostgreSQL advisory locks serialize processing for each symbol.
        # SQLite does not support these locks, so skip them in tests.
        if (
            db.bind is not None
            and db.bind.dialect.name == "postgresql"
        ):
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:symbol))"),
                {"symbol": payload.symbol},
            )

        # Check again after acquiring the PostgreSQL lock.
        existing = _find_existing_trade(
            db,
            payload.venue,
            payload.trade_id,
        )

        if existing:
            if not _same_trade(existing, payload):
                raise TradeConflict(
                    "This venue and trade ID already exist with different data."
                )

            return existing, False

        # Check the current position before accepting a SELL.
        position = get_position(db, payload.symbol)

        if (
            payload.side == "SELL"
            and payload.quantity > position["quantity"]
        ):
            raise TradeConflict(
                f"Cannot sell {payload.quantity}; current position is "
                f"{position['quantity']}."
            )

        trade = Trade(**payload.model_dump())
        db.add(trade)
        db.commit()
        db.refresh(trade)

        return trade, True

    except TradeConflict:
        db.rollback()
        raise

    except Exception:
        # A concurrent request may have inserted this trade first.
        db.rollback()

        existing = _find_existing_trade(
            db,
            payload.venue,
            payload.trade_id,
        )

        if existing:
            if _same_trade(existing, payload):
                return existing, False

            raise TradeConflict(
                "This venue and trade ID already exist with different data."
            )

        raise


def get_position(db: Session, symbol: str) -> dict:
    """
    Calculate position, average cost, and P&L using average-cost accounting.
    """

    trades = db.scalars(
        select(Trade)
        .where(Trade.symbol == symbol)
        .order_by(Trade.timestamp, Trade.id)
    ).all()

    quantity = Decimal("0")
    cost = Decimal("0")
    realized = Decimal("0")

    for trade in trades:
        if trade.side == "BUY":
            cost += trade.quantity * trade.price
            quantity += trade.quantity

        else:
            if trade.quantity > quantity:
                raise TradeConflict(
                    "Stored trades would produce a negative position."
                )

            average_cost = (
                cost / quantity if quantity else Decimal("0")
            )

            realized += trade.quantity * (
                trade.price - average_cost
            )

            cost -= average_cost * trade.quantity
            quantity -= trade.quantity

            if quantity == 0:
                cost = Decimal("0")

    average_cost = (
        cost / quantity if quantity else Decimal("0")
    )

    latest = db.get(LatestPrice, symbol)
    market_price = latest.price if latest else None

    unrealized = (
        quantity * (market_price - average_cost)
        if market_price is not None
        else None
    )

    return {
        "symbol": symbol,
        "quantity": quantity,
        "average_cost": average_cost,
        "realized_pnl": realized,
        "latest_price": market_price,
        "unrealized_pnl": unrealized,
    }


def set_latest_price(
    db: Session,
    symbol: str,
    price: Decimal,
) -> LatestPrice:
    """Create or update the latest market price for a symbol."""

    latest = db.get(LatestPrice, symbol)

    if latest:
        latest.price = price
    else:
        latest = LatestPrice(
            symbol=symbol,
            price=price,
        )
        db.add(latest)

    db.commit()
    db.refresh(latest)

    return latest


def reconcile_trades(
    db: Session,
    venue: str,
    external_trades: list[TradeCreate],
) -> dict:
    """
    Compare stored trades against an external venue statement.

    missing_from_storage: external trades absent from storage.
    extra_in_storage: stored trades absent from the statement.
    mismatched: matching trade IDs with different trade details.
    """

    stored_trades = db.scalars(
        select(Trade).where(Trade.venue == venue)
    ).all()

    stored = {
        trade.trade_id: trade
        for trade in stored_trades
    }

    external = {
        trade.trade_id: trade
        for trade in external_trades
    }

    missing = []
    extra = []
    mismatched = []

    def snapshot(trade) -> dict:
        return {
            "venue": trade.venue,
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": str(trade.quantity),
            "price": str(trade.price),
            "timestamp": _normalize_timestamp(
                trade.timestamp
            ).isoformat(),
        }

    # Identify external trades that are missing or mismatched.
    for trade_id, external_trade in external.items():
        stored_trade = stored.get(trade_id)

        if stored_trade is None:
            missing.append(snapshot(external_trade))
            continue

        if not _same_trade(stored_trade, external_trade):
            mismatched.append(
                {
                    "trade_id": trade_id,
                    "stored": snapshot(stored_trade),
                    "external": snapshot(external_trade),
                }
            )

    # Identify stored trades missing from the external statement.
    for trade_id, stored_trade in stored.items():
        if trade_id not in external:
            extra.append(snapshot(stored_trade))

    return {
        "venue": venue,
        "missing_from_storage": missing,
        "extra_in_storage": extra,
        "mismatched": mismatched,
    }
