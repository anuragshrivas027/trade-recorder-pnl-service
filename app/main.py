
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import LatestPrice, Trade
from app.schemas import (
    LatestPriceUpdate,
    ReconciliationRequest,
    TradeCreate,
    TradeResponse,
)
from app.services import (
    TradeConflict,
    get_position,
    reconcile_trades,
    record_trade,
    set_latest_price,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trade Recorder & PnL Service",
    description="Record trades, track positions, calculate PnL, and reconcile venue statements.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/trades", response_model=TradeResponse, status_code=201)
def create_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    try:
        trade, created = record_trade(db, payload)
        # A repeated identical trade returns the existing record.
        # The response header indicates whether a new record was created.
        from fastapi.responses import JSONResponse

        response_status = 201 if created else 200
        return JSONResponse(
            status_code=response_status,
            content=TradeResponse.model_validate(trade).model_dump(mode="json"),
        )
    except TradeConflict as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Trade conflicts with an existing record.",
        ) from exc


@app.get("/trades", response_model=list[TradeResponse])
def list_trades(db: Session = Depends(get_db)):
    return db.scalars(select(Trade).order_by(Trade.id)).all()


@app.get("/positions/{symbol}")
def read_position(symbol: str, db: Session = Depends(get_db)):
    return get_position(db, symbol.upper())


@app.put("/prices/{symbol}")
def update_latest_price(
    symbol: str,
    payload: LatestPriceUpdate,
    db: Session = Depends(get_db),
):
    latest = set_latest_price(db, symbol.upper(), payload.price)
    position = get_position(db, symbol.upper())

    return {
        "symbol": latest.symbol,
        "latest_price": latest.price,
        "position": position,
    }


@app.post("/reconciliation")
def reconcile_statement(
    payload: ReconciliationRequest,
    db: Session = Depends(get_db),
):
    return reconcile_trades(
        db,
        payload.venue,
        payload.trades,
    )
