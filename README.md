# PersonalFinanceAnalyzer

PersonalFinanceAnalyzer is a Streamlit web application for personal finance tracking, with authentication, uploads, transaction management, budgeting, and reporting.

## Current Structure

This is the current application structure in the repository:

- [main.py](main.py): active application entry point and page routing
- [app](app): core package (database, models, auth, repositories, services, UI helpers, utilities, reports)
- [views](views): page-level UI modules (Dashboard, Transactions, Upload, Budget, Reports)
- [src/db.py](src/db.py): legacy database helper retained for compatibility
- [src/services](src/services): legacy services retained (still covered by existing tests)
- [tests](tests): unit and integration tests

The previous src-based app entry and UI path is no longer the active runtime path.

## Architecture Notes

- Runtime starts from [main.py](main.py).
- Database initialization is handled by [app/database.py](app/database.py).
- Authentication is handled in [app/auth.py](app/auth.py).
- Page rendering is routed to [views/dashboard.py](views/dashboard.py), [views/transactions.py](views/transactions.py), [views/upload.py](views/upload.py), [views/budget.py](views/budget.py), and [views/reports.py](views/reports.py).

## Setup

Install dependencies with Poetry:

```bash
poetry install
```

If you need to start local Postgres from the project compose setup:

```bash
docker compose up -d db-dev
```

## Run

Start the Streamlit app:

```bash
poetry run streamlit run main.py
```

## Test

Run tests:

```bash
poetry run pytest -q
```

Run formatting and lint checks:

```bash
poetry run ruff format --check .
poetry run ruff check .
```

## Documentation

- [docs/adr.md](docs/adr.md)
- [docs/techstack.md](docs/techstack.md)
- [README_RUN.md](README_RUN.md)
