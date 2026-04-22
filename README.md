# PersonalFinanceAnalyzer

PersonalFinanceAnalyzer is a Streamlit web application for personal finance tracking. The current implementation includes authentication, transaction import, dashboard reporting, and a Docker Compose setup backed by PostgreSQL.

## Project Description

The application is being built incrementally around the documented user stories and acceptance criteria. Current functionality includes:
- user registration and login
- duplicate-email rejection
- logout and return to the dashboard entry state
- transaction import and categorization
- dashboard summaries and reporting
- confirmation email delivery hook via SMTP configuration

Architecture and stack decisions are documented in:
- [docs/adr.md](docs/adr.md)
- [docs/techstack.md](docs/techstack.md)

## How To Run

### Quick Start (Docker Compose - Recommended)

```bash
# Clone and setup
git clone https://github.com/BradleyB132/PersonalFinanceAnalyzer.git
cd PersonalFinanceAnalyzer
cp .env.example .env

# Start the app and database
docker compose up --build
```

Then open http://localhost:8501

### Alternative: Poetry Setup

Install dependencies with Poetry:

```bash
poetry install
```

If you need to start the included Postgres service only:

```bash
docker compose up -d db
```

Start the Streamlit app:

```bash
poetry run streamlit run src/app.py
```

The app will open a login/register page. Use the register tab to create a new account and the login tab to sign in.

## How To Run Tests

Run the test suite:

```bash
poetry run pytest
```

Run formatting and lint checks:

```bash
poetry run ruff format --check .
poetry run ruff check .
```

## Usage Examples

Registration flow:
1. Open the app.
2. Go to the Register tab.
3. Enter an email and password.
4. Submit the form.
5. If SMTP is configured, a confirmation email is sent. Otherwise, the app logs a preview and shows a warning.

Login flow:
1. Open the app.
2. Go to the Login tab.
3. Enter the registered email and password.
4. Submit the form.
5. On success, you are redirected to the dashboard view.

Example confirmation message:

```text
Welcome to PersonalFinanceAnalyzer, user@example.com! Your account has been created successfully. You can now log in and access your dashboard.
```

## Requirement Coverage

Implemented in this branch:
- user authentication flows
- transaction import and dashboard reporting
- architecture decision record and tech stack record
- unit, integration, and end-to-end style tests
- logging setup
- GitHub CI, Dependabot, and code security scanning workflow files
- PostgreSQL schema in `db/schema.sql`

Still requires manual GitHub/environment setup:
- main branch protection rules
- required PR reviews and code review policy
- GitHub Project backlog/sprint board
- production deployment target and uptime monitoring
- confirmation email SMTP configuration
