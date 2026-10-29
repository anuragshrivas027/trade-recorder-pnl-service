
## TradeLedger — Trade Recording & P&L Service

TradeLedger is a backend service built with **Python, FastAPI, and PostgreSQL** to record financial trades, track positions, calculate profit and loss (P&L), and reconcile internal trade records against external trading venue statements.

The project focuses on reliable trade ingestion, duplicate prevention, accurate financial calculations, and position validation.

## Features

- **Trade Ingestion:** Record BUY and SELL trades from different venues.
- **Input Validation:** Reject invalid trade sides, non-positive quantities, and non-positive prices.
- **Idempotency:** Prevent duplicate trades using the combination of venue and trade ID.
- **Position Tracking:** Calculate net quantity and average cost for each symbol.
- **Realized P&L:** Calculate profit or loss when a position is sold.
- **Unrealized P&L:** Calculate profit or loss using the latest market price.
- **Oversell Protection:** Reject SELL trades that exceed the available position.
- **Price Updates:** Create or update the latest market price for a symbol.
- **Trade Reconciliation:** Identify missing, extra, and mismatched trades.
- **Automated Testing:** Verify core API and trading logic using pytest.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL | Persistent database |
| SQLAlchemy | Database ORM |
| Pydantic | Request validation |
| psycopg | PostgreSQL driver |
| python-dotenv | Environment variable management |
| Uvicorn | Application server |
| pytest | Automated testing |
| HTTPX | API testing support |

## Project Structure

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

- `main.py` — Defines the FastAPI application and API endpoints.
- `database.py` — Configures the SQLAlchemy engine and database sessions.
- `models.py` — Defines the Trade and LatestPrice database models.
- `schemas.py` — Validates incoming requests and defines response schemas.
- `services.py` — Implements trade processing, position calculations, P&L, price updates, and reconciliation.
- `test_api.py` — Contains automated API tests.
- `.env` — Stores local database connection settings and must not be committed to Git.

## Prerequisites

Install the following software before running the project:

- Python
- PostgreSQL
- Git
- Visual Studio Code (recommended)

The project was developed on Windows 11 using Python 3.14.6 and PostgreSQL 17.11.

## Setup and Installation

### 1. Create the Project Directory

The project was created at:

```text
C:\TradeLedger
```

Open PowerShell or the VS Code terminal and navigate to the directory:

```powershell
cd C:\TradeLedger
```

### 2. Create and Activate a Virtual Environment

Create an isolated Python environment:

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

The terminal should display `(.venv)` when the environment is active.

### 3. Install Dependencies

Install the packages listed in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Start the PostgreSQL service and create a database named:

```text
tradeledger
```

The database can be created using pgAdmin or the PostgreSQL command-line tool.

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/tradeledger
```

Replace `USERNAME` and `PASSWORD` with your PostgreSQL credentials. URL-encode special characters in the password when required.

Do not commit `.env` to GitHub.

### 6. Verify the Database Connection

With the virtual environment activated, run:

```powershell
python -c "from app.database import engine; c = engine.connect(); print('Database:', engine.dialect.name); print('PostgreSQL connection successful!'); c.close()"
```

The expected database dialect is `postgresql`.

## Running the Application

Start the FastAPI development server:

```powershell
python -m uvicorn app.main:app --reload
```

The application runs at:

http://127.0.0.1:8000

Open the interactive Swagger documentation to test the API:

http://127.0.0.1:8000/docs

Stop the development server by pressing `Ctrl + C` in the terminal.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application health |
| POST | `/trades` | Records a new trade |
| GET | `/trades` | Retrieves recorded trades |
| GET | `/positions/{symbol}` | Retrieves position and P&L |
| PUT | `/prices/{symbol}` | Creates or updates the latest market price |
| POST | `/reconciliation` | Reconciles stored trades against an external statement |

Use Swagger UI at `/docs` to view the exact request schemas and execute API requests.

## Example Trade Request

Submit a BUY trade using `POST /trades`:

```json
{
  "venue": "test-venue",
  "trade_id": "TRADE-001",
  "symbol": "BTC-USD",
  "side": "BUY",
  "quantity": "10",
  "price": "100",
  "timestamp": "2026-10-29T10:00:00Z"
}
```

A newly recorded trade returns HTTP `201 Created`. An identical duplicate returns the existing trade rather than recording it again. Reusing the same venue and trade ID with different details is rejected.

## Position and P&L Calculation

TradeLedger uses the **average-cost method** to calculate positions and profit and loss.

Consider these trades:

| Action | Quantity | Price |
|---|---:|---:|
| BUY | 10 | 100 |
| BUY | 10 | 110 |
| SELL | 5 | 120 |

After these transactions, the expected position is:

| Metric | Value |
|---|---:|
| Remaining quantity | 15 |
| Average cost | 105 |
| Realized P&L | 75 |
| Latest market price | 125 |
| Unrealized P&L | 300 |

**Realized P&L**

Realized P&L is calculated when a position is sold.

`Realized P&L = Sold quantity × (Sell price − Average cost)`

For the example:

`5 × (120 − 105) = 75`

**Unrealized P&L**

Unrealized P&L is calculated using the remaining quantity and latest market price.

`Unrealized P&L = Remaining quantity × (Latest price − Average cost)`

For the example:

`15 × (125 − 105) = 300`

Financial calculations use Python's `Decimal` type and SQL `NUMERIC` columns to reduce floating-point precision errors.

## Trade Reconciliation

The reconciliation endpoint compares stored trades against an external venue statement.

It returns three categories:

- `missing_from_storage` — Trades present externally but absent from storage.
- `extra_in_storage` — Trades present in storage but absent from the external statement.
- `mismatched` — Trades with the same trade ID but different details.

The comparison includes the symbol, side, quantity, price, and timestamp.

## Oversell Protection

Before recording a SELL trade, the service checks the available position.

If the requested sell quantity exceeds the current position, the trade is rejected with an HTTP conflict response, and the rejected trade is not persisted.

## Running Automated Tests

Run the test suite from the project directory:

```powershell
python -m pytest -v
```

The current test suite contains seven tests covering:

1. Application health.
2. Rejection of non-positive quantities.
3. Duplicate trade prevention.
4. Average-cost and P&L calculations.
5. Oversell rejection and unchanged position.
6. Trade reconciliation.
7. Conflicting data for an existing trade ID.

**Verified result during development:** `7 passed, 0 failed`.

The automated tests use SQLite for isolated testing. The PostgreSQL connection and selected API scenarios were also checked manually. Dedicated PostgreSQL concurrency tests have not yet been completed.

## Documentation

- [DESIGN.md](DESIGN.md) — Architecture, data model, accounting method, and design decisions.
- [AI_USAGE.md](AI_USAGE.md) — Disclosure of AI assistance used during development.

## Security

- Database credentials are stored in `.env`.
- `.env` and `.venv/` are excluded from Git using `.gitignore`.
- Financial calculations use `Decimal`.
- The database enforces uniqueness on `(venue, trade_id)`.

Never commit passwords, credentials, or other secrets to the repository.

## Limitations and Future Improvements

- Add automated PostgreSQL integration and concurrent-request tests.
- Introduce database migrations using Alembic.
- Add API authentication and authorization.
- Improve logging, monitoring, and error handling.
- Expand accounting and reconciliation edge-case coverage.

## Repository

GitHub: https://github.com/anuragshrivas027/TradeLedger

## Author

**Anurag Shrivas**
