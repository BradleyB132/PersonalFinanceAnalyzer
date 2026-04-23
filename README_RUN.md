# Running PersonalFinanceAnalyzer (using Poetry)

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

1. **Start the application:**
   ```bash
   docker-compose up -d
   ```

2. **Install Playwright browsers:**
   ```bash
   poetry run playwright install
   ```

3. **Run E2E tests:**
   ```bash
   poetry run pytest tests/e2e/ -v
   ```

4. **Run tests in headed mode (see browser):**
   ```bash
   poetry run pytest tests/e2e/ --headed
   ```

**Note:** E2E tests require the app to be running. They automatically create test users and clean up after each test.

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
