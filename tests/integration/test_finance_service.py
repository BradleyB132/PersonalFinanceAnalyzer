from __future__ import annotations

from io import BytesIO

import pandas as pd

from services.finance_service import (
    build_pdf_report,
    build_transactions_csv,
    calculate_budget_recommendations,
    get_category_summary,
    get_transactions,
    import_statement_file,
    search_transactions,
    update_transaction_category,
)


def _statement_csv() -> bytes:
    frame = pd.DataFrame(
        [
            {"date": "2024-01-03", "details": "Whole Foods Market", "amount": -42.15},
            {"date": "2024-01-05", "details": "Train Ticket", "amount": -18.50},
        ]
    )
    buffer = BytesIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()


def test_import_statement_and_category_resolution(finance_engine) -> None:
    result = import_statement_file(
        finance_engine,
        user_id=1,
        file_name="statement.csv",
        file_type="bank_statement",
        file_bytes=_statement_csv(),
    )

    assert result.inserted_count == 2

    transactions = get_transactions(finance_engine, 1)
    assert len(transactions) == 2
    assert set(transactions["category"].astype(str)) == {"Groceries", "Uncategorized"}

    summary = get_category_summary(finance_engine, 1)
    groceries = summary[summary["category"] == "Groceries"].iloc[0]
    assert float(groceries["amount"]) == -42.15


def test_search_update_and_exports(finance_engine) -> None:
    import_statement_file(
        finance_engine,
        user_id=1,
        file_name="statement.csv",
        file_type="bank_statement",
        file_bytes=_statement_csv(),
    )

    transactions = get_transactions(finance_engine, 1)
    target_id = int(transactions.iloc[0]["id"])

    search_results = search_transactions(finance_engine, 1, keyword="train")
    assert len(search_results) == 1
    assert search_results.iloc[0]["description"] == "Train Ticket"

    updated = update_transaction_category(finance_engine, 1, target_id, 3)
    assert updated

    updated_transactions = get_transactions(finance_engine, 1)
    updated_row = updated_transactions[updated_transactions["id"] == target_id].iloc[0]
    assert updated_row["category"] == "Travel"

    csv_bytes = build_transactions_csv(finance_engine, 1)
    pdf_bytes = build_pdf_report(finance_engine, 1)
    assert len(csv_bytes) > 20
    assert pdf_bytes.startswith(b"%PDF")


def test_budget_recommendations_use_priority_categories(finance_engine) -> None:
    import_statement_file(
        finance_engine,
        user_id=1,
        file_name="statement.csv",
        file_type="bank_statement",
        file_bytes=_statement_csv(),
    )

    recommendations = calculate_budget_recommendations(
        finance_engine,
        user_id=1,
        monthly_income=2000.0,
        priority_categories=["Travel"],
    )

    assert not recommendations.empty
    assert set(recommendations.columns) == {
        "category",
        "actual_spend",
        "weight",
        "recommended_budget",
        "priority",
        "overspent",
        "variance",
    }
    assert recommendations[recommendations["category"] == "Travel"]["priority"].iloc[0]