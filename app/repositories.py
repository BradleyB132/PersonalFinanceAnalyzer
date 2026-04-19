"""
Repository layer - data access operations.
Each function receives a SQLAlchemy session.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Transaction, Category, UploadedFile, Budget


def list_categories(session: Session, user_id: int) -> list[Category]:
    """Get all categories available to a user (system + user-specific)."""
    return session.query(Category).filter(
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    ).order_by(Category.name).all()


def get_category_by_id(session: Session, cat_id: int) -> Optional[Category]:
    return session.query(Category).filter(Category.id == cat_id).first()


def create_user_category(session: Session, user_id: int, name: str) -> Category:
    category = Category(name=name, user_id=user_id, is_system=False)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def create_uploaded_file(
    session: Session, user_id: int, file_type: str, file_name: str
) -> UploadedFile:
    uf = UploadedFile(user_id=user_id, file_type=file_type, file_name=file_name)
    session.add(uf)
    session.commit()
    session.refresh(uf)
    return uf


def insert_transactions(
    session: Session,
    user_id: int,
    source: str,
    uploaded_file_id: int,
    transactions: list[dict],
    category_id_resolver,
) -> int:
    """Insert parsed transactions. category_id_resolver(description) -> int."""
    count = 0
    for txn in transactions:
        cat_id = category_id_resolver(txn["description"])
        session.add(Transaction(
            user_id=user_id,
            description=txn["description"],
            amount=txn["amount"],
            transaction_date=txn["transaction_date"],
            category_id=cat_id,
            uploaded_file_id=uploaded_file_id,
            source=source,
        ))
        count += 1
    session.commit()
    return count


def list_transactions(
    session: Session,
    user_id: int,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    source: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> list[Transaction]:
    """Get transactions with optional filters."""
    q = session.query(Transaction).filter(Transaction.user_id == user_id)
    if search:
        q = q.filter(Transaction.description.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if source:
        q = q.filter(Transaction.source == source)
    if start_date:
        q = q.filter(Transaction.transaction_date >= start_date)
    if end_date:
        q = q.filter(Transaction.transaction_date <= end_date)
    if min_amount is not None:
        q = q.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(Transaction.amount <= max_amount)
    return q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()


def update_transaction_category(
    session: Session, user_id: int, transaction_id: int, new_category_id: int
) -> bool:
    txn = session.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.user_id == user_id
    ).first()
    if not txn:
        return False
    txn.category_id = new_category_id
    session.commit()
    return True


def delete_transaction(session: Session, user_id: int, transaction_id: int) -> bool:
    txn = session.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.user_id == user_id
    ).first()
    if not txn:
        return False
    session.delete(txn)
    session.commit()
    return True


def get_or_create_budget(session: Session, user_id: int) -> Budget:
    budget = session.query(Budget).filter(Budget.user_id == user_id).first()
    if not budget:
        budget = Budget(user_id=user_id, monthly_income=0.0, priority_categories="")
        session.add(budget)
        session.commit()
        session.refresh(budget)
    return budget


def update_budget(
    session: Session, user_id: int, monthly_income: float, priority_categories: str = ""
) -> Budget:
    budget = get_or_create_budget(session, user_id)
    budget.monthly_income = monthly_income
    budget.priority_categories = priority_categories
    session.commit()
    session.refresh(budget)
    return budget
