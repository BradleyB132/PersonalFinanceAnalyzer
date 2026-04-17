"""Finance and transaction service helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
import math
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from db import execute_query, execute_write, fetch_one

STATEMENT_REQUIRED_COLUMNS = {
    "amount",
    "description",
    "transaction_date",
}

COLUMN_ALIASES = {
    "date": "transaction_date",
    "transaction date": "transaction_date",
    "transactiondate": "transaction_date",
    "posted date": "transaction_date",
    "posted_date": "transaction_date",
    "details": "description",
    "memo": "description",
    "payee": "description",
    "merchant": "description",
    "narrative": "description",
    "transaction description": "description",
    "debit": "debit",
    "withdrawal": "debit",
    "charge": "debit",
    "credit": "credit",
    "deposit": "credit",
    "payment": "credit",
    "amount": "amount",
    "description": "description",
    "transaction_date": "transaction_date",
}


@dataclass(frozen=True)
class StatementImportResult:
    uploaded_file_id: int
    inserted_count: int
    skipped_count: int
    file_type: str


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.copy()
    renamed.columns = [
        str(column).strip().lower().replace("-", " ") for column in renamed.columns
    ]
    renamed = renamed.rename(
        columns={
            column: COLUMN_ALIASES.get(column, column) for column in renamed.columns
        }
    )
    return renamed


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid transaction date: {value}")
    return parsed.date()


def _coerce_amount(value: Any) -> float:
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("$", "")
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = f"-{cleaned[1:-1]}"
        try:
            return float(cleaned)
        except ValueError as exc:
            raise ValueError(f"Invalid amount: {value}") from exc

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid amount: {value}") from exc


def _derive_amount_from_debit_credit(frame: pd.DataFrame) -> pd.DataFrame:
    derived = frame.copy()
    if "amount" in derived.columns:
        return derived

    if "debit" not in derived.columns and "credit" not in derived.columns:
        return derived

    debit_series = (
        derived["debit"].apply(_coerce_amount)
        if "debit" in derived.columns
        else pd.Series([0.0] * len(derived), index=derived.index)
    )
    credit_series = (
        derived["credit"].apply(_coerce_amount)
        if "credit" in derived.columns
        else pd.Series([0.0] * len(derived), index=derived.index)
    )

    # Debit-like values are treated as outgoing spend (negative), credits as inflow (positive).
    derived["amount"] = credit_series - debit_series.abs()
    return derived


def _statement_frame_from_bytes(file_bytes: bytes) -> pd.DataFrame:
    frame = pd.read_csv(BytesIO(file_bytes))
    frame = _normalize_columns(frame)
    frame = _derive_amount_from_debit_credit(frame)
    missing = STATEMENT_REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            "CSV must contain columns: " + ", ".join(sorted(STATEMENT_REQUIRED_COLUMNS))
        )
    return frame[list(STATEMENT_REQUIRED_COLUMNS)]


def get_available_categories(engine, user_id: int) -> pd.DataFrame:
    rows = execute_query(
        """
        SELECT id, name, user_id
        FROM categories
        WHERE user_id IS NULL OR user_id = :user_id
        ORDER BY CASE WHEN user_id IS NULL THEN 0 ELSE 1 END, name ASC
        """,
        {"user_id": user_id},
        engine=engine,
    )
    return pd.DataFrame(rows)


def ensure_uncategorized_category(engine) -> int:
    existing = fetch_one(
        "SELECT id FROM categories WHERE name = 'Uncategorized' AND user_id IS NULL",
        engine=engine,
    )
    if existing is not None:
        return int(existing["id"])

    execute_write(
        "INSERT INTO categories (name, user_id) VALUES (:name, NULL)",
        {"name": "Uncategorized"},
        engine=engine,
    )
    created = fetch_one(
        "SELECT id FROM categories WHERE name = 'Uncategorized' AND user_id IS NULL ORDER BY id DESC",
        engine=engine,
    )
    if created is None:
        raise RuntimeError("Unable to create Uncategorized category")
    return int(created["id"])


def get_rules(engine, user_id: int) -> list[dict[str, Any]]:
    return execute_query(
        """
        SELECT keyword, category_id, user_id
        FROM description_rules
        WHERE user_id IS NULL OR user_id = :user_id
        ORDER BY CASE WHEN user_id IS NULL THEN 1 ELSE 0 END, keyword ASC
        """,
        {"user_id": user_id},
        engine=engine,
    )


def resolve_category_id(engine, user_id: int, description: str) -> int:
    lowered_description = description.lower()
    for rule in get_rules(engine, user_id):
        keyword = str(rule["keyword"]).lower()
        if keyword and keyword in lowered_description:
            return int(rule["category_id"])
    return ensure_uncategorized_category(engine)


def import_statement_file(
    engine,
    user_id: int,
    file_name: str,
    file_type: str,
    file_bytes: bytes,
) -> StatementImportResult:
    frame = _statement_frame_from_bytes(file_bytes)

    execute_write(
        """
        INSERT INTO uploaded_files (user_id, file_type, file_name)
        VALUES (:user_id, :file_type, :file_name)
        """,
        {"user_id": user_id, "file_type": file_type, "file_name": file_name},
        engine=engine,
    )
    uploaded = fetch_one(
        """
        SELECT id
        FROM uploaded_files
        WHERE user_id = :user_id AND file_type = :file_type AND file_name = :file_name
        ORDER BY id DESC
        """,
        {"user_id": user_id, "file_type": file_type, "file_name": file_name},
        engine=engine,
    )
    if uploaded is None:
        raise RuntimeError("Unable to create uploaded file record")
    uploaded_file_id = int(uploaded["id"])

    inserted_count = 0
    skipped_count = 0
    for record in frame.to_dict(orient="records"):
        description = str(record["description"]).strip()
        category_id = resolve_category_id(engine, user_id, description)
        amount = _coerce_amount(record["amount"])
        transaction_date = _coerce_date(record["transaction_date"])
        result = execute_write(
            """
            INSERT INTO transactions (
                user_id,
                category_id,
                amount,
                description,
                transaction_date,
                uploaded_file_id
            )
            SELECT
                :user_id,
                :category_id,
                :amount,
                :description,
                :transaction_date,
                :uploaded_file_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM transactions t
                WHERE t.user_id = :user_id
                  AND DATE(t.transaction_date) = :transaction_date
                  AND LOWER(TRIM(t.description)) = LOWER(TRIM(:description))
                  AND t.amount = :amount
            )
            """,
            {
                "user_id": user_id,
                "category_id": category_id,
                "amount": amount,
                "description": description,
                "transaction_date": transaction_date,
                "uploaded_file_id": uploaded_file_id,
            },
            engine=engine,
        )
        if result.rowcount > 0:
            inserted_count += 1
        else:
            skipped_count += 1

    return StatementImportResult(
        uploaded_file_id=uploaded_file_id,
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        file_type=file_type,
    )


def get_transactions(engine, user_id: int) -> pd.DataFrame:
    rows = execute_query(
        """
        SELECT
            t.id,
            t.user_id,
            t.amount,
            t.description,
            t.transaction_date,
            c.name AS category,
            c.id AS category_id,
            t.uploaded_file_id,
            COALESCE(uf.file_type, 'manual') AS source_type
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        LEFT JOIN uploaded_files uf ON uf.id = t.uploaded_file_id
        WHERE t.user_id = :user_id
        ORDER BY t.transaction_date DESC, t.id DESC
        """,
        {"user_id": user_id},
        engine=engine,
    )
    return pd.DataFrame(rows)


def get_transaction_by_id(
    engine, user_id: int, transaction_id: int
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, user_id, amount, description, transaction_date, category_id, uploaded_file_id
        FROM transactions
        WHERE user_id = :user_id AND id = :transaction_id
        """,
        {"user_id": user_id, "transaction_id": transaction_id},
        engine=engine,
    )


def update_transaction_category(
    engine, user_id: int, transaction_id: int, category_id: int
) -> bool:
    result = execute_write(
        """
        UPDATE transactions
        SET category_id = :category_id
        WHERE user_id = :user_id AND id = :transaction_id
        """,
        {
            "user_id": user_id,
            "transaction_id": transaction_id,
            "category_id": category_id,
        },
        engine=engine,
    )
    return result.rowcount > 0


def search_transactions(
    engine,
    user_id: int,
    keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> pd.DataFrame:
    where_clauses = ["t.user_id = :user_id"]
    params: dict[str, Any] = {"user_id": user_id}

    if keyword:
        where_clauses.append("LOWER(t.description) LIKE :keyword")
        params["keyword"] = f"%{keyword.lower()}%"
    if start_date:
        where_clauses.append("DATE(t.transaction_date) >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("DATE(t.transaction_date) <= :end_date")
        params["end_date"] = end_date
    if category_id:
        where_clauses.append("t.category_id = :category_id")
        params["category_id"] = category_id
    if min_amount is not None:
        where_clauses.append("t.amount >= :min_amount")
        params["min_amount"] = min_amount
    if max_amount is not None:
        where_clauses.append("t.amount <= :max_amount")
        params["max_amount"] = max_amount

    rows = execute_query(
        f"""
        SELECT
            t.id,
            t.user_id,
            t.amount,
            t.description,
            t.transaction_date,
            c.name AS category,
            c.id AS category_id,
            t.uploaded_file_id,
            COALESCE(uf.file_type, 'manual') AS source_type
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        LEFT JOIN uploaded_files uf ON uf.id = t.uploaded_file_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY t.transaction_date DESC, t.id DESC
        """,
        params,
        engine=engine,
    )
    return pd.DataFrame(rows)


def get_category_summary(engine, user_id: int) -> pd.DataFrame:
    rows = execute_query(
        """
        SELECT c.id AS category_id, c.name AS category, COALESCE(SUM(t.amount), 0) AS amount
        FROM categories c
        LEFT JOIN transactions t ON t.category_id = c.id AND t.user_id = :user_id
        WHERE c.user_id IS NULL OR c.user_id = :user_id
        GROUP BY c.id, c.name
        HAVING COALESCE(SUM(t.amount), 0) != 0 OR c.name = 'Uncategorized'
        ORDER BY amount DESC, category ASC
        """,
        {"user_id": user_id},
        engine=engine,
    )
    return pd.DataFrame(rows)


def get_trend_summary(engine, user_id: int) -> pd.DataFrame:
    dialect_name = engine.dialect.name
    if dialect_name == "sqlite":
        period_expression = "strftime('%Y-%m', t.transaction_date)"
    else:
        period_expression = "to_char(t.transaction_date, 'YYYY-MM')"

    rows = execute_query(
        f"""
        SELECT {period_expression} AS period, COALESCE(SUM(t.amount), 0) AS amount
        FROM transactions t
        WHERE t.user_id = :user_id
        GROUP BY period
        ORDER BY period ASC
        """,
        {"user_id": user_id},
        engine=engine,
    )
    return pd.DataFrame(rows)


def get_dashboard_metrics(engine, user_id: int) -> dict[str, Any]:
    transactions = get_transactions(engine, user_id)
    categories = get_category_summary(engine, user_id)
    total_amount = (
        float(transactions["amount"].sum()) if not transactions.empty else 0.0
    )
    return {
        "transaction_count": int(len(transactions)),
        "category_count": int(len(categories)),
        "total_amount": total_amount,
        "average_amount": float(transactions["amount"].mean())
        if not transactions.empty
        else 0.0,
    }


def build_transactions_csv(engine, user_id: int) -> bytes:
    frame = get_transactions(engine, user_id)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "id",
                "user_id",
                "amount",
                "description",
                "transaction_date",
                "category",
                "category_id",
                "uploaded_file_id",
                "source_type",
            ]
        )
    return frame.to_csv(index=False).encode("utf-8")


def build_pdf_report(engine, user_id: int) -> bytes:
    metrics = get_dashboard_metrics(engine, user_id)
    category_summary = get_category_summary(engine, user_id)
    trend_summary = get_trend_summary(engine, user_id)
    transactions = get_transactions(engine, user_id).head(10)

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("PersonalFinanceAnalyzer Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Transactions: {metrics['transaction_count']}", styles["Normal"]),
        Paragraph(f"Categories: {metrics['category_count']}", styles["Normal"]),
        Paragraph(f"Total Amount: {metrics['total_amount']:.2f}", styles["Normal"]),
        Paragraph(f"Average Amount: {metrics['average_amount']:.2f}", styles["Normal"]),
        Spacer(1, 12),
    ]

    if not category_summary.empty:
        story.append(Paragraph("Category Summary", styles["Heading2"]))
        category_table = [["Category", "Amount"]] + [
            [row["category"], f"{float(row['amount']):.2f}"]
            for _, row in category_summary.iterrows()
        ]
        table = Table(category_table, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.extend([table, Spacer(1, 12)])

    if not trend_summary.empty:
        story.append(Paragraph("Trend Summary", styles["Heading2"]))
        trend_table = [["Period", "Amount"]] + [
            [row["period"], f"{float(row['amount']):.2f}"]
            for _, row in trend_summary.iterrows()
        ]
        table = Table(trend_table, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.extend([table, Spacer(1, 12)])

    if not transactions.empty:
        story.append(Paragraph("Recent Transactions", styles["Heading2"]))
        tx_table = [["Date", "Description", "Category", "Amount"]] + [
            [
                str(row["transaction_date"]),
                str(row["description"]),
                str(row["category"]),
                f"{float(row['amount']):.2f}",
            ]
            for _, row in transactions.iterrows()
        ]
        table = Table(tx_table, hAlign="LEFT", colWidths=[80, 220, 120, 80])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(table)

    document.build(story)
    return buffer.getvalue()


def calculate_budget_recommendations(
    engine,
    user_id: int,
    monthly_income: float,
    priority_categories: list[str] | None = None,
) -> pd.DataFrame:
    if not math.isfinite(monthly_income) or monthly_income <= 0:
        raise ValueError("Monthly income must be a positive number")

    categories = get_available_categories(engine, user_id)
    category_summary = get_category_summary(engine, user_id)
    if categories.empty:
        return pd.DataFrame(
            columns=[
                "category",
                "actual_spend",
                "weight",
                "recommended_budget",
                "priority",
                "overspent",
                "variance",
            ]
        )

    merged = categories[["id", "name"]].rename(columns={"name": "category"}).copy()
    merged = merged.merge(
        category_summary[["category", "amount"]], on="category", how="left"
    )
    merged["amount"] = pd.to_numeric(merged["amount"], errors="coerce").fillna(0.0)
    merged["spend_basis"] = merged["amount"].abs()

    spend_total = float(merged["spend_basis"].sum())
    if spend_total > 0:
        merged["weight"] = merged["spend_basis"] / spend_total
    else:
        merged["weight"] = 1.0 / len(merged)

    priority_set = {category.lower() for category in (priority_categories or [])}
    merged["priority"] = merged["category"].str.lower().isin(priority_set)
    merged["weight"] = merged.apply(
        lambda row: row["weight"] * (1.15 if row["priority"] else 1.0), axis=1
    )
    weight_total = float(merged["weight"].sum())
    if weight_total <= 0 or not math.isfinite(weight_total):
        merged["weight"] = 1.0 / len(merged)
    else:
        merged["weight"] = merged["weight"] / weight_total

    merged["recommended_budget"] = merged["weight"] * monthly_income
    merged["overspent"] = merged["spend_basis"] > merged["recommended_budget"]
    merged["variance"] = merged["recommended_budget"] - merged["spend_basis"]
    merged = merged.sort_values(["overspent", "spend_basis"], ascending=[False, False])
    return merged[
        [
            "category",
            "spend_basis",
            "weight",
            "recommended_budget",
            "priority",
            "overspent",
            "variance",
        ]
    ].rename(columns={"spend_basis": "actual_spend"})
