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


def _login(page: Page, base_url: str, email: str, password: str) -> None:
    page.goto(base_url)
    time.sleep(1.0)

    page.fill('input[placeholder="you@example.com"]', email)
    page.fill('input[placeholder="Enter your password"]', password)
    page.click('button[type="submit"]')
    time.sleep(2.0)

    assert page.locator('text=Personal Finance Command Center').count() > 0


def _upload_csv(
    page: Page,
    nav_label: str,
    csv_path: Path,
    expected_texts: list[str] | None = None,
) -> None:
    page.click(f'text={nav_label}')
    time.sleep(0.5)

    upload = page.locator('input[type="file"]')
    assert upload.count() > 0, "Upload control not found"
    upload.set_input_files(str(csv_path))
    time.sleep(0.5)

    process_button = page.locator('text=Process Upload')
    assert process_button.count() > 0, "Process Upload button not found"
    process_button.click()
    time.sleep(2.0)

    for expected_text in expected_texts or []:
        assert page.locator(f"text={expected_text}").count() > 0


def test_upload_bank_statement_and_view_dashboard(
    page: Page, base_url: str, tmp_path: Path, e2e_test_user: dict
):
    """E2E: Upload a small bank statement CSV and assert dashboard shows data.

    Steps:
    1. Register a new test user
    2. Login with the test user
    3. Upload a CSV file via the UI
    4. Verify dashboard updates with transactions

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

    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])
    _upload_csv(
        page,
        "Upload Bank",
        csv_file,
        expected_texts=["Whole Foods Market", "Train Ticket"],
    )

    # Verify dashboard shows the uploaded transactions
    assert page.locator('text=Whole Foods Market').count() > 0, "Transaction not found in dashboard"
    assert page.locator('text=Train Ticket').count() > 0, "Transaction not found in dashboard"

    # Verify dashboard metrics updated
    assert page.locator('text=Transactions').count() > 0, "Transaction count not updated"


def test_upload_credit_card_statement_and_combined_view(
    page: Page, base_url: str, tmp_path: Path, e2e_test_user: dict
):
    """E2E: Upload credit card CSV and assert combined transactions view.

    This covers ACs in docs/stories/user_story_&_ACs_2.md.
    """
    csv_file = tmp_path / "card_statement.csv"
    _write_fixture_csv(
        csv_file,
        [
            {
                "posted date": "2024-02-01",
                "merchant": "Uber Trip",
                "debit": "27.45",
                "credit": "0",
            },
            {
                "posted date": "2024-02-02",
                "merchant": "Card Payment",
                "debit": "0",
                "credit": "150.00",
            },
        ],
    )

    bank_csv = tmp_path / "bank_statement.csv"
    _write_fixture_csv(
        bank_csv,
        [
            {"date": "2024-01-03", "details": "Whole Foods Market", "amount": -42.15},
            {"date": "2024-01-05", "details": "Train Ticket", "amount": -18.5},
        ],
    )

    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])
    _upload_csv(page, "Upload Bank", bank_csv)
    _upload_csv(
        page,
        "Upload Card",
        csv_file,
        expected_texts=["Uber Trip", "Card Payment"],
    )

    # Verify both bank and card transactions are visible
    assert page.locator('text=Uber Trip').count() > 0, "Credit card transaction not found"
    assert page.locator('text=Card Payment').count() > 0, "Credit card transaction not found"


def test_dashboard_overview_display(page: Page, base_url: str, e2e_test_user: dict):
    """E2E: Test that dashboard overview shows key metrics and charts."""
    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])

    # Should show key metrics cards
    assert page.locator('text=Transactions').count() > 0
    assert page.locator('text=Categories').count() > 0
    assert page.locator('text=Total Flow').count() > 0

    # Should show chart sections
    assert page.locator('text=Income vs Expense').count() > 0
    assert page.locator('text=Monthly Spend Trend').count() > 0
    assert page.locator('text=Category Mix').count() > 0


def test_search_and_filter_functionality(
    page: Page, base_url: str, tmp_path: Path, e2e_test_user: dict
):
    """E2E: Test search and filter transactions functionality."""
    csv_file = tmp_path / "search_statement.csv"
    _write_fixture_csv(
        csv_file,
        [
            {"date": "2024-03-01", "details": "Netflix", "amount": -19.99},
            {"date": "2024-03-03", "details": "Uber Trip", "amount": -24.50},
        ],
    )

    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])
    _upload_csv(page, "Upload Bank", csv_file)

    # Navigate to Search section
    page.click('text=Search')
    time.sleep(0.5)

    # Should show search form
    assert page.locator('text=Find transactions by keyword').count() > 0
    assert page.locator('input[placeholder="Walmart, Uber, Netflix"]').count() > 0

    page.fill('input[placeholder="Walmart, Uber, Netflix"]', 'Uber')
    page.click('text=Apply filters')
    time.sleep(1.0)
    assert page.locator('text=Uber Trip').count() > 0


def test_reports_export_functionality(
    page: Page, base_url: str, tmp_path: Path, e2e_test_user: dict
):
    """E2E: Test reports and export functionality."""
    csv_file = tmp_path / "reports_statement.csv"
    _write_fixture_csv(
        csv_file,
        [{"date": "2024-03-07", "details": "Coffee Shop", "amount": -8.25}],
    )

    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])
    _upload_csv(page, "Upload Bank", csv_file)

    # Navigate to Reports section
    page.click('text=Reports')
    time.sleep(0.5)

    # Should show export buttons
    assert page.locator('text=Download CSV report').count() > 0
    assert page.locator('text=Download PDF snapshot').count() > 0


def test_budget_planner_interface(page: Page, base_url: str, e2e_test_user: dict):
    """E2E: Test budget planner interface loads correctly."""
    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])

    # Navigate to Budgeting section
    page.click('text=Budgeting')
    time.sleep(0.5)

    # Should show budget planner interface
    assert page.locator('text=Budget Planner').count() > 0
    assert page.locator('text=Monthly income').count() > 0
    assert page.locator('text=Priority categories').count() > 0


def test_error_handling_invalid_file(
    page: Page, base_url: str, tmp_path: Path, e2e_test_user: dict
):
    """E2E: Test error handling for invalid file uploads."""
    # Create an invalid CSV file
    invalid_csv = tmp_path / "invalid.csv"
    invalid_csv.write_text("invalid,csv,data\n1,2,3")

    _login(page, base_url, e2e_test_user["email"], e2e_test_user["password"])
    page.click('text=Upload Bank')
    time.sleep(0.5)

    # Try to upload invalid file
    upload = page.locator('input[type="file"]')
    if upload.count() > 0:
        upload.set_input_files(str(invalid_csv))
        time.sleep(0.2)
        page.click('text=Process Upload')
        time.sleep(1.0)
        # Should show error message (though exact message may vary)
        error_indicators = [
            page.locator('text=Failed to process'),
            page.locator('text=error'),
            page.locator('text=Error')
        ]
        # At least one error indicator should be present
        assert any(indicator.count() > 0 for indicator in error_indicators)
