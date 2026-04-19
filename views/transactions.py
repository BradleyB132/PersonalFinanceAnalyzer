"""Transactions view - list, search, filter, edit category."""
import streamlit as st
import pandas as pd

from app.database import get_session
from app import repositories as repo
from app.ui import render_header


def render():
    render_header(
        "Transactions",
        "View, search, filter and manage your transactions"
    )

    session = get_session()
    user_id = st.session_state["user_id"]

    try:
        if "txn_filters_open" not in st.session_state:
            st.session_state.txn_filters_open = True

        categories = repo.list_categories(session, user_id)
        cat_options = {c.id: c.name for c in categories}
        cat_name_options = ["All categories"] + [c.name for c in categories]

        category_id = None
        source = None
        start_date = None
        end_date = None
        min_amt = None
        max_amt = None

        # --- Filters ---
        with st.container(border=True):
            search_col, toggle_col = st.columns([5, 1.6])
            with search_col:
                search = st.text_input(
                    "Search", placeholder="Search by description...",
                    label_visibility="collapsed", key="txn_search"
                )

            with toggle_col:
                toggle_label = (
                    ":material/expand_less: Hide Filters"
                    if st.session_state.txn_filters_open
                    else ":material/tune: Show Filters"
                )
                if st.button(toggle_label, key="txn_toggle_filters", use_container_width=True):
                    st.session_state.txn_filters_open = not st.session_state.txn_filters_open
                    st.rerun()

            if st.session_state.txn_filters_open:
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    cat_choice = st.selectbox(
                        "Category", cat_name_options, key="txn_cat"
                    )
                    if cat_choice != "All categories":
                        for cid, cname in cat_options.items():
                            if cname == cat_choice:
                                category_id = cid
                                break

                    src_choice = st.selectbox(
                        "Source", ["All", "bank", "credit_card"],
                        key="txn_src"
                    )
                    if src_choice != "All":
                        source = src_choice

                with cc2:
                    start_date = st.date_input(
                        "Start date", value=None, key="txn_start"
                    )
                    end_date = st.date_input(
                        "End date", value=None, key="txn_end"
                    )

                with cc3:
                    min_amt_str = st.text_input(
                        "Min amount", placeholder="e.g. -1000", key="txn_min"
                    )
                    max_amt_str = st.text_input(
                        "Max amount", placeholder="e.g. 5000", key="txn_max"
                    )
                    try:
                        min_amt = float(min_amt_str) if min_amt_str else None
                    except ValueError:
                        min_amt = None
                    try:
                        max_amt = float(max_amt_str) if max_amt_str else None
                    except ValueError:
                        max_amt = None

        # --- Transactions ---
        txns = repo.list_transactions(
            session,
            user_id=user_id,
            search=search or None,
            category_id=category_id,
            source=source,
            start_date=start_date or None,
            end_date=end_date or None,
            min_amount=min_amt,
            max_amount=max_amt,
        )

        st.markdown(
            f"**{len(txns)} transaction{'s' if len(txns) != 1 else ''}**"
        )

        if not txns:
            st.info("No transactions match your filters. Upload a statement to get started.")
            return

        # Build the dataframe for editing
        rows = []
        for t in txns:
            rows.append({
                "id": t.id,
                "Date": t.transaction_date,
                "Description": t.description,
                "Category": cat_options.get(t.category_id, "Uncategorized"),
                "Source": t.source.replace("_", " ").title() if t.source else "",
                "Amount": t.amount,
            })

        df = pd.DataFrame(rows)

        # Show editable table with selectbox for category
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None,  # hide id
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Description": st.column_config.TextColumn(
                    "Description", disabled=True, width="large"
                ),
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=list(cat_options.values()),
                    required=True,
                ),
                "Source": st.column_config.TextColumn(
                    "Source", disabled=True
                ),
                "Amount": st.column_config.NumberColumn(
                    "Amount", format="$%.2f", disabled=True
                ),
            },
            use_container_width=True,
            hide_index=True,
            key="txn_editor",
        )

        # Detect category changes and persist
        changes = 0
        name_to_id = {v: k for k, v in cat_options.items()}
        for i, row in edited_df.iterrows():
            original = df.iloc[i]
            if row["Category"] != original["Category"]:
                new_cat_id = name_to_id.get(row["Category"])
                if new_cat_id:
                    repo.update_transaction_category(
                        session, user_id, int(row["id"]), new_cat_id
                    )
                    changes += 1

        if changes > 0:
            st.success(f"Updated {changes} transaction categor{'ies' if changes > 1 else 'y'}")
            st.rerun()

    finally:
        session.close()
