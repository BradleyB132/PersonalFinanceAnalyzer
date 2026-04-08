"""
Main Streamlit application for PersonalFinanceAnalyzer.

This module implements a minimal Streamlit UI that allows users to:
- connect to a PostgreSQL database using DATABASE_URL from .env
- view transactions
- upload a CSV file of transactions (simple parsing)
- run basic auto-categorization using description rules

All database access uses SQLAlchemy engine and raw SQL for simplicity.

Time complexity notes:
- Loading all transactions: O(N) where N is number of transactions returned
- Categorization: O(M * R) where M is number of new transactions and R is number of rules (simple linear scan)

Space complexity notes:
- Uses O(N) memory to hold fetched rows in pandas DataFrame for display

"""

import os
import io
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env values into environment variables
load_dotenv()

# Create DB engine using DATABASE_URL from .env
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is not set in environment. Please check .env file')

engine = create_engine(DATABASE_URL)


def get_transactions(user_id=1, limit=200):
    """Fetch recent transactions for a user from the database.

    Args:
        user_id (int): ID of the user to fetch transactions for.
        limit (int): Maximum number of rows to fetch.

    Returns:
        pd.DataFrame: DataFrame containing transaction rows.

    Complexity:
        Time: O(N) where N is the number of rows returned (bounded by limit)
        Space: O(N)
    """
    query = text(
        """
        SELECT t.id, t.user_id, t.amount, t.description, t.transaction_date, c.name as category
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = :user_id
        ORDER BY t.transaction_date DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"user_id": user_id, "limit": limit})
    return df


def get_description_rules(user_id=1):
    """Load description rules for user and global rules.

    Returns:
        list of tuples: (keyword, category_id)

    Complexity:
        Time: O(R)
        Space: O(R)
    """
    query = text(
        """
        SELECT keyword, category_id, user_id
        FROM description_rules
        WHERE user_id = :user_id OR user_id IS NULL
        ORDER BY user_id DESC
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).fetchall()
    # Return list in priority order (user-specific first)
    return [(r[0], r[1]) for r in rows]


def apply_rules_to_description(description, rules):
    """Apply description rules to map a description to a category id.

    This performs a case-insensitive substring match against each rule keyword.
    Complexity: O(R * L) where R is number of rules and L is length of description.
    """
    desc_lower = description.lower()
    for keyword, category_id in rules:
        if keyword.lower() in desc_lower:
            return category_id
    return None


def insert_transaction(user_id, category_id, amount, description, transaction_date, uploaded_file_id=None):
    """Insert a new transaction into the DB using a parameterized query.

    Ensures connections are closed via context manager.
    Complexity: O(1)
    """
    query = text(
        """
        INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id)
        VALUES (:user_id, :category_id, :amount, :description, :transaction_date, :uploaded_file_id)
        RETURNING id
        """
    )
    with engine.connect() as conn:
        result = conn.execute(query, {
            "user_id": user_id,
            "category_id": category_id,
            "amount": amount,
            "description": description,
            "transaction_date": transaction_date,
            "uploaded_file_id": uploaded_file_id,
        })
        inserted_id = result.scalar()
        conn.commit()
    return inserted_id


# Streamlit UI
st.title('Personal Finance Analyzer - Minimal')

st.markdown('Simple demo application to view and upload transactions')

user_id = st.sidebar.number_input('User ID', min_value=1, value=1)

if st.sidebar.button('Refresh Transactions'):
    st.experimental_rerun()

st.header('Recent Transactions')
try:
    df = get_transactions(user_id=user_id)
    st.dataframe(df)
except Exception as e:
    st.error(f'Error loading transactions: {e}')

st.header('Upload Transactions CSV')
uploaded_file = st.file_uploader('Upload CSV', type=['csv'])

if uploaded_file is not None:
    # Read CSV into pandas safely
    csv_bytes = uploaded_file.read()
    try:
        df_new = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as e:
        st.error(f'Failed to parse CSV: {e}')
        df_new = None

    if df_new is not None:
        st.write('Preview of uploaded file:')
        st.dataframe(df_new.head())

        if st.button('Process Upload'):
            # Basic required columns enforcement
            required_cols = {'amount', 'description', 'transaction_date'}
            if not required_cols.issubset(set(df_new.columns)):
                st.error(f'CSV must contain columns: {required_cols}')
            else:
                rules = get_description_rules(user_id=user_id)
                inserted = 0
                for _, row in df_new.iterrows():
                    # Determine category via rules
                    category = apply_rules_to_description(str(row['description']), rules)
                    if category is None:
                        category = 1  # Fallback to 'Uncategorized' id
                    # Insert into DB
                    try:
                        insert_transaction(
                            user_id=user_id,
                            category_id=category,
                            amount=float(row['amount']),
                            description=str(row['description']),
                            transaction_date=str(row['transaction_date']),
                            uploaded_file_id=None,
                        )
                        inserted += 1
                    except Exception as e:
                        st.error(f'Failed to insert row: {e}')
                st.success(f'Inserted {inserted} transactions')
                st.experimental_rerun()
