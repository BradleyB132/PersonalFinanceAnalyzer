# PersonalFinanceAnalyzer

PersonalFinanceAnalyzer is a Streamlit web application for personal finance tracking. The current implementation on the `login` branch provides a working registration and login flow backed by the existing `users` table in `db/schema.sql`.

## Project Description

The application is being built incrementally around the documented user stories and acceptance criteria. Current auth functionality includes:
- user registration
- login with email and password
- duplicate-email rejection
- logout and return to the homepage/dashboard entry state
- confirmation email delivery hook via SMTP configuration

Architecture and stack decisions are documented in:
- [docs/adr.md](docs/adr.md)
- [docs/techstack.md](docs/techstack.md)

## How To Build

Install dependencies with Poetry:

```bash
poetry install
```

If you need to refresh the database environment, start the included Postgres service:

```bash
docker compose up -d db-dev
```

## How To Run

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
- user stories and acceptance criteria for authentication
- architecture decision record and tech stack record
- unit, integration, and end-to-end style tests for auth logic
- logging setup
- GitHub CI, Dependabot, and code security scanning workflow files
- PostgreSQL schema in `db/schema.sql`
- login, registration, and logout behavior in the Streamlit app

Still requires manual GitHub/environment setup:
- main branch protection rules
- required PR reviews and code review policy
- GitHub Project backlog/sprint board
- production deployment target and uptime monitoring
- confirmation email SMTP configuration
