
# TradeLedger — System Design

## 1. Overview

TradeLedger is a REST API service for recording financial trades, tracking positions, calculating profit and loss (P&L), and reconciling trade records.

The application is built using Python and FastAPI, with PostgreSQL as the primary database. SQLAlchemy is used for database operations, and Pydantic is used for request validation.

## 2. Technology Stack

- **Language:** Python
- **API Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Database Driver:** Psycopg
- **Testing:** Pytest and HTTPX
- **Server:** Uvicorn

## 3. Architecture

The application follows a layered structure.

1. **API Layer:** Defines HTTP endpoints and handles incoming requests.
2. **Validation Layer:** Validates request data, including trade side, quantity, and price.
3. **Service Layer:** Implements trade recording, duplicate detection, position calculations, P&L calculations, and reconciliation.
4. **Database Layer:** Manages database connections and SQLAlchemy sessions.
5. **Persistence Layer:** Stores trades and the latest market prices in database tables.

### Request Flow

A client sends an HTTP request to a FastAPI endpoint. The request is validated, and the relevant service logic processes it. The service reads or updates database records and returns the result through the API.

## 4. Project Structure

```text
TradeLedger/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── services.py
├── tests/
│   └── test_api.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── DESIGN.md
└── AI_USAGE.md
```

The `.env` file contains local configuration and must not be committed to version control.

## 5. Data Model

### Trade

The Trade table stores recorded transactions.

Important fields include:

- `id`: Internal database identifier.
- `venue`: Trading venue or source.
- `trade_id`: Identifier supplied by the trading source.
- `symbol`: Instrument symbol.
- `side`: BUY or SELL.
- `quantity`: Number of units traded.
- `price`: Execution price per unit.
- `timestamp`: Time of the trade.

The combination of `venue` and `trade_id` is unique. This helps prevent the same source trade from being recorded more than once.

### Latest Price

The Latest Price table stores the most recently recorded market price for each symbol. This price is used to calculate unrealized profit and loss.

## 6. Trade Recording and Idempotency

When a trade is submitted, the service checks whether a trade with the same venue and trade ID already exists.

- If the same trade is submitted again with identical details, it is treated as a duplicate rather than recorded twice.
- If the same identifier is submitted with different details, the request is rejected.
- New valid trades are stored in the database.

This behavior makes retrying requests safer and prevents duplicate trades from affecting positions twice.

## 7. Position and P&L Calculations

TradeLedger uses an average-cost approach for calculating positions.

### Average Cost

For a BUY trade:

`New Average Cost = ((Old Quantity × Old Average Cost) + (Bought Quantity × Buy Price)) / New Quantity`

For a SELL trade, the average cost of the remaining position stays unchanged.

### Realized P&L

For a SELL trade:

`Realized P&L = Sold Quantity × (Sell Price − Average Cost)`

### Unrealized P&L

For an open position:

`Unrealized P&L = Current Quantity × (Latest Market Price − Average Cost)`

If the position has no remaining quantity, its open-position unrealized P&L is zero.

SELL trades that exceed the available position are rejected.

## 8. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check application health |
| POST | `/trades` | Record a trade |
| GET | `/trades` | Retrieve recorded trades |
| GET | `/positions/{symbol}` | Retrieve position and P&L |
| PUT | `/prices/{symbol}` | Update the latest market price |
| POST | `/reconciliation` | Compare trade records |

## 9. Reconciliation

The reconciliation endpoint compares supplied trade records against stored records and identifies missing records, extra records, and records whose details do not match.

This helps detect differences between the internal ledger and an external trade source.

## 10. Validation and Error Handling

The API validates trade quantities and prices, restricts trade sides to BUY or SELL, and rejects invalid requests.

It also handles duplicate trade identifiers and prevents selling more units than the current position. FastAPI returns appropriate HTTP error responses for rejected requests.

## 11. Database and Consistency

SQLAlchemy manages database access. Database constraints help enforce uniqueness, while database transactions protect related updates.

The service uses a PostgreSQL advisory lock for trade processing when running against PostgreSQL to help serialize relevant position-changing operations. This is intended to reduce concurrency-related inconsistencies.

The current automated tests use an isolated SQLite test database. PostgreSQL-specific concurrency behavior should also be tested against PostgreSQL before production deployment.

## 12. Testing

The automated test suite covers:

- Health endpoint behavior.
- Validation of invalid quantities.
- Duplicate trade handling.
- Average-cost and P&L calculations.
- Rejection of overselling.
- Reconciliation differences.
- Rejection of conflicting duplicate trade identifiers.

The current test suite passes all seven tests.

## 13. Security and Limitations

Database credentials are loaded from environment configuration and must not be committed to GitHub.

This project is a take-home implementation. Before production use, additional work would be needed for authentication, authorization, structured logging, monitoring, database migration management, deployment configuration, and more extensive concurrency and integration testing.
