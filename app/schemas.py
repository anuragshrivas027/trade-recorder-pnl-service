
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradeCreate(BaseModel):
    venue: str = Field(min_length=1, max_length=100)
    trade_id: str = Field(min_length=1, max_length=150)
    symbol: str = Field(min_length=1, max_length=50)
    side: Literal["BUY", "SELL"]
    quantity: Decimal = Field(gt=0, max_digits=24, decimal_places=8)
    price: Decimal = Field(gt=0, max_digits=24, decimal_places=8)
    timestamp: datetime

    @field_validator("venue", "trade_id", "symbol")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("side", mode="before")
    @classmethod
    def normalize_side(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue: str
    trade_id: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


class LatestPriceUpdate(BaseModel):
    price: Decimal = Field(gt=0, max_digits=24, decimal_places=8)


class ReconciliationRequest(BaseModel):
    venue: str = Field(min_length=1, max_length=100)
    trades: list[TradeCreate]


class ReconciliationDifference(BaseModel):
    venue: str
    trade_id: str
    difference: str
    stored: dict | None = None
    external: dict | None = None
