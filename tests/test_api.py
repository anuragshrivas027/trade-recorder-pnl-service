
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def trade(
    trade_id: str,
    side: str,
    quantity: str,
    price: str,
    venue: str = "binance",
):
    return {
        "venue": venue,
        "trade_id": trade_id,
        "symbol": "BTC-USD",
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def post_trade(client, payload):
    return client.post("/trades", json=payload)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_trade_validation_rejects_non_positive_quantity(client):
    response = post_trade(
        client,
        trade("T-INVALID", "BUY", "0", "100"),
    )
    assert response.status_code == 422


def test_duplicate_trade_is_not_counted_twice(client):
    payload = trade("T-DUPLICATE", "BUY", "10", "100")

    first = post_trade(client, payload)
    second = post_trade(client, payload)

    assert first.status_code == 201
    assert second.status_code == 200

    trades = client.get("/trades").json()
    assert len(trades) == 1


def test_average_cost_and_pnl(client):
    assert post_trade(
        client, trade("T1", "BUY", "10", "100")
    ).status_code == 201

    assert post_trade(
        client, trade("T2", "BUY", "10", "110")
    ).status_code == 201

    assert post_trade(
        client, trade("T3", "SELL", "5", "120")
    ).status_code == 201

    price_response = client.put(
        "/prices/BTC-USD",
        json={"price": "125"},
    )
    assert price_response.status_code == 200

    position = client.get("/positions/BTC-USD").json()

    assert Decimal(str(position["quantity"])) == Decimal("15")
    assert Decimal(str(position["average_cost"])) == Decimal("105")
    assert Decimal(str(position["realized_pnl"])) == Decimal("75")
    assert Decimal(str(position["unrealized_pnl"])) == Decimal("300")


def test_oversell_is_rejected_and_position_unchanged(client):
    assert post_trade(
        client, trade("T-BUY", "BUY", "10", "100")
    ).status_code == 201

    response = post_trade(
        client, trade("T-SELL", "SELL", "11", "120")
    )
    assert response.status_code == 409

    position = client.get("/positions/BTC-USD").json()
    assert Decimal(str(position["quantity"])) == Decimal("10")


def test_reconciliation_finds_missing_extra_and_mismatched_trades(client):
    assert post_trade(
        client, trade("T1", "BUY", "10", "100")
    ).status_code == 201

    assert post_trade(
        client, trade("T2", "BUY", "5", "101")
    ).status_code == 201

    external_trades = [
        trade("T1", "BUY", "10", "100"),
        trade("T2", "BUY", "6", "101"),
        trade("T3", "BUY", "1", "99"),
    ]

    response = client.post(
        "/reconciliation",
        json={
            "venue": "binance",
            "trades": external_trades,
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert [item["trade_id"] for item in result["missing_from_storage"]] == ["T3"]
    assert result["extra_in_storage"] == []
    assert [item["trade_id"] for item in result["mismatched"]] == ["T2"]


def test_same_id_with_different_data_is_rejected(client):
    first = trade("T-SAME", "BUY", "10", "100")
    second = trade("T-SAME", "BUY", "10", "101")

    assert post_trade(client, first).status_code == 201
    assert post_trade(client, second).status_code == 409
