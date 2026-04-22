"""End-to-end (E2E) tests using Playwright.

These tests exercise the web UI via a browser automation layer and validate the
user stories for uploading bank and credit card statements and viewing the
resulting dashboard. Tests are intentionally verbose with comments to help a
junior engineer understand what's being validated and why.

Notes:
- Playwright must be installed and browsers installed via `playwright install`.
- Running these tests in CI requires a headless display environment (default
  for Playwright in CI) and may require additional setup for network DB access.

Complexity:
- E2E tests are slower than unit tests (typically seconds per test). Keep them
  focused on critical user flows to limit runtime.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import pytest
from playwright.sync_api import Page

# Directory where test fixtures (CSV files) are kept
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return base URL for the running Streamlit app under test.

    Tests assume the developer starts the app locally on port 8501 by running:
    `poetry run streamlit run src/app.py`.
    """
    return os.getenv("E2E_BASE_URL", "http://localhost:8501")


def _write_fixture_csv(path: Path, rows: list[dict]) -> None:
    """Helper to write a small CSV used by the UI upload control.

    Keeping fixtures generated inside tests avoids committing any sample data
    and makes tests more self-contained.
    """
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)


def test_upload_bank_statement_and_view_dashboard(page: Page, base_url: str, tmp_path: Path):
    """E2E: Upload a small bank statement CSV and assert dashboard shows data.

    Steps:
    1. Open the app and register a new test user (if registration is available).
    2. Login with the test user.
    3. Use the sidebar upload control to pick a CSV file.
    4. Process the upload and assert the dashboard updates with transactions.

    These steps focus on ACs in docs/stories/user_story_&_ACs_1.md.
    """
    # Prepare a test CSV with two transactions that will be auto-categorized
    csv_file = tmp_path / "bank_statement.csv"
    _write_fixture_csv(
        csv_file,
        [
            {"date": "2024-01-03", "details": "Whole Foods Market", "amount": -42.15},
            {"date": "2024-01-05", "details": "Train Ticket", "amount": -18.5},
        ],
    )

    # Navigate to the app
    page.goto(base_url)
    time.sleep(0.5)

    # If app shows Register/Login, register and login programmatically via UI
    # For brevity we assume a simple flow: if "Sign in" exists, it's login page
    if page.locator("text=Sign in").count() > 0:
        page.fill('input[placeholder="you@example.com"]', 'e2e_user@example.com')
        page.fill('input[type="password"]', 'Password123!')
        page.click('text=Sign in')
        time.sleep(0.5)

    # After login, the dashboard should be visible. Use the sidebar upload control
    # located by placeholder text.
    upload = page.locator('input[type="file"]')
    assert upload.count() > 0, "Upload control not present in sidebar"

    # Set the file input to our generated CSV. Playwright supports set_input_files.
    upload.set_input_files(str(csv_file))
    time.sleep(0.2)

    # Click the "Process Upload" button in the main area
    page.click('text=Process Upload')
    time.sleep(1.5)

    # Assert that the dashboard now displays a transaction table containing
    # "Whole Foods Market". We search the page content for that text.
    assert page.locator('text=Whole Foods Market').count() > 0
    assert page.locator('text=Train Ticket').count() > 0


def test_upload_credit_card_statement_and_combined_view(page: Page, base_url: str, tmp_path: Path):
    """E2E: Upload credit card CSV and assert combined transactions view.

    This covers ACs in docs/stories/user_story_&_ACs_2.md.
    """
    csv_file = tmp_path / "card_statement.csv"
    _write_fixture_csv(
        csv_file,
        [
            {"posted date": "2024-02-01", "merchant": "Uber Trip", "debit": "27.45", "credit": "0"},
            {"posted date": "2024-02-02", "merchant": "Card Payment", "debit": "0", "credit": "150.00"},
        ],
    )

    page.goto(base_url)
    time.sleep(0.5)

    # Assume user is already logged in from prior test or performs login
    upload = page.locator('input[type="file"]')
    assert upload.count() > 0
    upload.set_input_files(str(csv_file))
    time.sleep(0.2)
    page.click('text=Process Upload')
    time.sleep(1.5)

    # The combined view should now include both the bank and card transactions
    assert page.locator('text=Uber Trip').count() > 0
    assert page.locator('text=Card Payment').count() > 0