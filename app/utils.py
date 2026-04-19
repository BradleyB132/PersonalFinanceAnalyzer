"""
Utility functions for:
- CSV and PDF statement parsing
- Default categories and rules seeding
- Auto-categorization logic
"""
import io
import csv
import re
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
import pdfplumber

from app.models import Category, DescriptionRule, Transaction


DEFAULT_CATEGORIES = [
    {"name": "Groceries", "keywords": ["grocery", "supermarket", "walmart", "kroger", "safeway", "costco", "whole foods", "trader joe", "aldi"]},
    {"name": "Dining", "keywords": ["restaurant", "cafe", "starbucks", "mcdonald", "chipotle", "uber eats", "doordash", "grubhub", "pizza"]},
    {"name": "Transportation", "keywords": ["uber", "lyft", "gas", "shell", "chevron", "parking", "transit", "metro", "fuel"]},
    {"name": "Utilities", "keywords": ["electric", "water", "gas bill", "internet", "phone", "verizon", "at&t", "comcast", "utility"]},
    {"name": "Shopping", "keywords": ["amazon", "target", "best buy", "apple", "nike", "clothing", "mall", "ebay"]},
    {"name": "Entertainment", "keywords": ["netflix", "spotify", "hulu", "movie", "concert", "gaming", "steam", "disney"]},
    {"name": "Healthcare", "keywords": ["pharmacy", "doctor", "hospital", "cvs", "walgreens", "medical", "dental", "clinic"]},
    {"name": "Travel", "keywords": ["airline", "hotel", "airbnb", "booking", "expedia", "flight", "marriott"]},
    {"name": "Subscriptions", "keywords": ["subscription", "membership", "annual fee", "monthly fee"]},
    {"name": "Income", "keywords": ["salary", "payroll", "deposit", "transfer in", "refund"]},
    {"name": "Uncategorized", "keywords": []},
]


def seed_default_categories(session: Session):
    """Create default system categories and rules if they don't exist."""
    for cat_data in DEFAULT_CATEGORIES:
        existing = session.query(Category).filter(
            Category.name == cat_data["name"],
            Category.user_id.is_(None)
        ).first()

        if not existing:
            category = Category(name=cat_data["name"], user_id=None, is_system=True)
            session.add(category)
            session.flush()
        else:
            category = existing

        # Add keywords as rules
        for keyword in cat_data["keywords"]:
            rule_exists = session.query(DescriptionRule).filter(
                DescriptionRule.keyword == keyword.lower(),
                DescriptionRule.user_id.is_(None)
            ).first()
            if not rule_exists:
                session.add(DescriptionRule(
                    keyword=keyword.lower(),
                    category_id=category.id,
                    user_id=None
                ))

    session.commit()


def auto_categorize(session: Session, description: str, user_id: int) -> Optional[int]:
    """Return the category_id for a transaction description based on rules."""
    desc_lower = description.lower()

    # Check user-specific rules first
    user_rules = session.query(DescriptionRule).filter(
        DescriptionRule.user_id == user_id
    ).all()
    for rule in user_rules:
        if rule.keyword in desc_lower:
            return rule.category_id

    # Check global rules
    global_rules = session.query(DescriptionRule).filter(
        DescriptionRule.user_id.is_(None)
    ).all()
    for rule in global_rules:
        if rule.keyword in desc_lower:
            return rule.category_id

    # Fallback to Uncategorized
    uncategorized = session.query(Category).filter(
        Category.name == "Uncategorized",
        Category.user_id.is_(None)
    ).first()
    return uncategorized.id if uncategorized else None


def parse_date(date_str: str) -> Optional[date]:
    """Try multiple date formats and return a date object."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_csv_statement(content: str) -> list[dict]:
    """Parse CSV content into a list of transaction dicts."""
    transactions = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            # Flexible column naming
            date_val = (row.get('Date') or row.get('date')
                        or row.get('Transaction Date') or row.get('Posted Date') or '')
            desc_val = (row.get('Description') or row.get('description')
                        or row.get('Memo') or row.get('Name') or '')
            amount_val = (row.get('Amount') or row.get('amount')
                          or row.get('Debit') or row.get('Credit') or '0')

            amount_str = re.sub(r'[^\d.\-]', '', str(amount_val))
            try:
                amount = float(amount_str) if amount_str else 0.0
            except ValueError:
                amount = 0.0

            parsed_date = parse_date(date_val)
            if desc_val and parsed_date:
                transactions.append({
                    "description": desc_val.strip(),
                    "amount": amount,
                    "transaction_date": parsed_date,
                })
    except Exception as e:
        print(f"CSV parse error: {e}")
    return transactions


def parse_pdf_statement(file_bytes: bytes) -> list[dict]:
    """Parse a PDF statement into a list of transaction dicts."""
    transactions = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    # Match date + amount patterns
                    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})', line)
                    amount_match = re.search(r'[-]?\$?[\d,]+\.\d{2}', line)
                    if date_match and amount_match:
                        amount_str = re.sub(r'[^\d.\-]', '', amount_match.group())
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            continue
                        desc_start = date_match.end()
                        desc_end = amount_match.start()
                        description = line[desc_start:desc_end].strip()
                        parsed_date = parse_date(date_match.group())
                        if description and parsed_date and len(description) > 2:
                            transactions.append({
                                "description": description,
                                "amount": amount,
                                "transaction_date": parsed_date,
                            })
    except Exception as e:
        print(f"PDF parse error: {e}")
    return transactions


def format_currency(value: float) -> str:
    """Format a number as USD currency."""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"
