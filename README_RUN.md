# Running PersonalFinanceAnalyzer

## 🚀 Quick Start with Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which sets up PostgreSQL and the app automatically.

### Prerequisites:
- Docker and Docker Compose
- Git

### Quickstart:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BradleyB132/PersonalFinanceAnalyzer.git
   cd PersonalFinanceAnalyzer
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Open your browser:**
   - App: http://localhost:8501
   - Database: localhost:5432 (postgres/postgres)

### Development with Hot Reload:

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## 🐍 Alternative: Running with Poetry

Prerequisites:
- Python 3.9+
- Poetry (https://python-poetry.org/)
- PostgreSQL reachable via `DATABASE_URL` in `.env`

Quickstart using Poetry:

1. Install Poetry (if not already installed):

   - macOS / Linux: `curl -sSL https://install.python-poetry.org | python3 -`
   - Windows: follow the Windows installer instructions on the Poetry website.

2. Initialize a Poetry project (if the repository does not already contain `pyproject.toml`):

   ```bash
   poetry init --no-interaction
   ```

3. Add runtime dependencies using Poetry:

   ```bash
   poetry add streamlit SQLAlchemy psycopg2-binary python-dotenv pandas
   ```

4. Install dependencies and spawn a virtual environment shell:

   ```bash
   poetry install
   poetry shell
   ```

5. Ensure `.env` contains the `DATABASE_URL` connection string (this repo already includes a sample `.env`).

6. Initialize the local database (optional):

   - Use `db/schema.sql` to create tables and `db/seed.sql` to populate sample data in your Postgres instance.

7. Run the Streamlit app via Poetry:

   ```bash
   poetry run streamlit run src/app.py
   ```

E2E tests (Playwright)
-----------------------

1. Install Playwright browsers and pytest plugin:

   ```bash
   poetry add --group dev pytest-playwright
   poetry run playwright install
   ```

2. Run E2E tests with pytest:

   ```bash
   poetry run pytest tests/e2e -q
   ```

Note: Running Playwright tests requires the app to be running locally (default http://localhost:8501) and accessible to the browser instance. Use `E2E_BASE_URL` environment variable to change the address if needed.

Notes:
- The app uses SQLAlchemy `create_engine` to connect to the database using `DATABASE_URL`.
- If you prefer not to use Poetry, you can still use a venv and `pip install -r requirements.txt`.
