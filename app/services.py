"""
Services layer - business logic and orchestration.
Combines repositories, utils, and domain rules.
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import repositories as repo
from app.models import Transaction, Category
from app.utils import (
    auto_categorize, parse_csv_statement, parse_pdf_statement,
)


def process_uploaded_statement(
    session: Session,
    user_id: int,
    file_name: str,
    file_bytes: bytes,
    source: str,  # 'bank' or 'credit_card'
) -> tuple[int, str]:
    """Process an uploaded file: parse, categorize, save.
    Returns: (count_saved, message)
    """
    lname = file_name.lower()
    if lname.endswith(".csv"):
        content = file_bytes.decode("utf-8", errors="ignore")
        parsed = parse_csv_statement(content)
    elif lname.endswith(".pdf"):
        parsed = parse_pdf_statement(file_bytes)
    else:
        return 0, "Unsupported file format. Please upload CSV or PDF."

    if not parsed:
        return 0, "No transactions could be parsed from the file."

    uploaded = repo.create_uploaded_file(session, user_id, source, file_name)

    def resolver(desc: str) -> Optional[int]:
        return auto_categorize(session, desc, user_id)

    count = repo.insert_transactions(
        session, user_id, source, uploaded.id, parsed, resolver
    )
    return count, f"Imported {count} transactions"


def compute_dashboard_stats(session: Session, user_id: int) -> dict:
    """Compute aggregate stats and chart data for the dashboard."""
    txns = session.query(Transaction).filter(Transaction.user_id == user_id).all()

    if not txns:
        return {
            "total_transactions": 0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_balance": 0.0,
            "by_category": [],
            "trends": [],
        }

    # Load categories in one shot
    cats = session.query(Category).all()
    cat_name_by_id = {c.id: c.name for c in cats}

    total_income = sum(t.amount for t in txns if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in txns if t.amount < 0))

    # By category (expenses only)
    by_cat: dict[str, float] = {}
    for t in txns:
        if t.amount < 0:
            name = cat_name_by_id.get(t.category_id, "Uncategorized")
            by_cat[name] = by_cat.get(name, 0.0) + abs(t.amount)

    by_category = [
        {"name": k, "value": round(v, 2)}
        for k, v in sorted(by_cat.items(), key=lambda x: -x[1])
    ]

    # Monthly trends
    monthly: dict[str, dict] = {}
    for t in txns:
        if not t.transaction_date:
            continue
        key = t.transaction_date.strftime("%Y-%m")
        m = monthly.setdefault(key, {"income": 0.0, "expenses": 0.0})
        if t.amount >= 0:
            m["income"] += t.amount
        else:
            m["expenses"] += abs(t.amount)

    trends = [
        {"month": k, "income": round(v["income"], 2), "expenses": round(v["expenses"], 2)}
        for k, v in sorted(monthly.items())
    ]

    return {
        "total_transactions": len(txns),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_income - total_expenses, 2),
        "by_category": by_category,
        "trends": trends,
    }


def compute_budget_recommendations(session: Session, user_id: int) -> dict:
    """Compute budget recommendations using the 50/30/20 rule.

    Analysis uses the most recent month with transactions (falls back to
    current calendar month if user has none). This gives useful feedback
    when analyzing historical statements instead of silently showing $0.
    """
    budget = repo.get_or_create_budget(session, user_id)
    monthly_income = budget.monthly_income or 0.0

    # Find the most recent month that has transactions
    latest_txn = session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.amount < 0,
    ).order_by(Transaction.transaction_date.desc()).first()

    if latest_txn and latest_txn.transaction_date:
        analysis_date = latest_txn.transaction_date
    else:
        analysis_date = date.today()

    start_of_month = analysis_date.replace(day=1)
    # Compute end of month (exclusive)
    if start_of_month.month == 12:
        end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        end_of_month = start_of_month.replace(month=start_of_month.month + 1)

    txns = session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_of_month,
        Transaction.transaction_date < end_of_month,
        Transaction.amount < 0,
    ).all()

    cats = session.query(Category).all()
    cat_by_id = {c.id: c.name for c in cats}

    spent_by_cat: dict[str, float] = {}
    for t in txns:
        name = cat_by_id.get(t.category_id, "Uncategorized")
        spent_by_cat[name] = spent_by_cat.get(name, 0.0) + abs(t.amount)

    # 50/30/20
    needs_cats = {"Groceries", "Utilities", "Transportation", "Healthcare"}
    wants_cats = {"Dining", "Shopping", "Entertainment", "Subscriptions"}

    needs_spent = sum(v for k, v in spent_by_cat.items() if k in needs_cats)
    wants_spent = sum(v for k, v in spent_by_cat.items() if k in wants_cats)

    recommendations = []
    alerts = []
    if monthly_income > 0:
        needs_budget = monthly_income * 0.50
        wants_budget = monthly_income * 0.30
        savings_budget = monthly_income * 0.20

        recommendations = [
            {
                "category": "Needs (50%)",
                "budget": round(needs_budget, 2),
                "spent": round(needs_spent, 2),
                "remaining": round(needs_budget - needs_spent, 2),
            },
            {
                "category": "Wants (30%)",
                "budget": round(wants_budget, 2),
                "spent": round(wants_spent, 2),
                "remaining": round(wants_budget - wants_spent, 2),
            },
            {
                "category": "Savings (20%)",
                "budget": round(savings_budget, 2),
                "spent": 0.0,
                "remaining": round(savings_budget, 2),
            },
        ]

        avg_budget = monthly_income * 0.10
        for cat, spent in spent_by_cat.items():
            if spent > avg_budget * 1.5 and avg_budget > 0:
                alerts.append({
                    "category": cat,
                    "message": f"Spending in {cat} is high this month",
                    "spent": round(spent, 2),
                })

    current_spending = [
        {"name": k, "value": round(v, 2)}
        for k, v in sorted(spent_by_cat.items(), key=lambda x: -x[1])
    ]

    return {
        "monthly_income": monthly_income,
        "recommendations": recommendations,
        "alerts": alerts,
        "current_spending": current_spending,
        "analysis_month": start_of_month.strftime("%B %Y"),
        "has_transactions": len(txns) > 0,
    }
